"""Tool resolver capability — locates executables and runner candidates."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from modules.shared.src.common.taxonomy_core_constant import TOOL_RUNNERS
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.contract_tool_protocol import IToolExecutor
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec
from modules.shared.src.xdg.utility_xdg_paths import bin_home


class ToolResolver(IToolExecutor):
    """Resolve a ToolSpec to a runnable executable and run it in-process.

    # Block 1: Constructor & spec resolution
    # Block 2: Executable discovery (bin_home + runner candidates)
    # Block 3: Execution
    """

    # -- Block 1: Constructor & spec resolution -------------------------------
    def __init__(self) -> None:
        self._root = repo_root()

    def resolve_spec(
        self,
        *,
        id: str,
        category: str,
        binary: str,
        is_mcp: bool,
        description: str,
        path: str,
        alias: str | None,
        mcp_binary: str | None,
        runner: str | None = None,
    ) -> ToolSpec:
        """Build a ToolSpec; runner falls back to the TOOL_RUNNERS map."""
        return ToolSpec(
            id=id,
            category=category,
            binary=binary,
            is_mcp=is_mcp,
            description=description,
            path=path,
            alias=alias,
            mcp_binary=mcp_binary,
            runner=runner or TOOL_RUNNERS.get(id, ""),
        )

    # -- Block 2: Executable discovery ----------------------------------------
    def find_executable(self, spec: ToolSpec) -> Path | None:
        """PATH win, then bin_home; internal tools fall back to runner candidates."""
        found = shutil.which(spec.binary)
        if found:
            return Path(found)
        local = bin_home() / spec.binary
        if local.exists() and os.access(local, os.X_OK):
            return local
        # Runner candidates for internal tools that are source-ready
        if spec.category == "internal":
            tool_dir = self._root / spec.path
            if spec.runner == "cargo" and shutil.which("cargo") and (tool_dir / "Cargo.toml").exists():
                return tool_dir / "Cargo.toml"
            if spec.runner in {"uv", "python"} and tool_dir.exists():
                if shutil.which("uv"):
                    return tool_dir
                if shutil.which("python3"):
                    return Path(spec.id)
        return None

    def executable_path(self, spec: ToolSpec) -> Path | None:
        """Return the runnable binary path, or None when not installed."""
        return self.find_executable(spec)

    # -- Block 3: Execution ----------------------------------------------------
    def run(self, spec: ToolSpec, args: list[str]) -> int:
        """Run the tool binary (or runner) with args; return 1 when not runnable.

        TODO(AES-CLI): replace os.execvpe with subprocess so the orchestrator
        can still own post-run reporting.
        """
        exe = self.find_executable(spec)
        if exe is not None:
            tool_dir = self._root / spec.path
            if spec.category == "internal" and spec.runner == "cargo" and exe == tool_dir / "Cargo.toml":
                os.execvpe("cargo", ["cargo", "run", "--quiet", "--manifest-path",
                                     str(exe), "--bin", f"{spec.id}-arwaky-cli", "--", *args], os.environ)
            elif spec.category == "internal" and spec.runner in {"uv", "python"} and exe == tool_dir:
                os.execvpe("uv", ["uv", "run", "--directory", str(tool_dir), spec.binary, *args], os.environ)
            elif spec.category == "internal" and spec.runner in {"uv", "python"} and exe == Path(spec.id):
                os.execvpe("python3", ["python3", "-m", spec.id, *args], os.environ)
            else:
                os.execvpe(str(exe), [str(exe), *args], os.environ)
        return 1
