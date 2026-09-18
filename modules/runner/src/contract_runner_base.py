"""Shared runner capability base class (contract layer — taxonomy-only deps)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from modules.shared.src.taxonomy_paths_constant import REPO_ROOT as repo_root
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.shared.src.taxonomy_tool_vo import ToolSpec


class RunnerBase:
    """Common resolver helpers every per-tool runner capability reuses.

    # Block 1: Executable discovery (PATH, bin_home, runner candidates)
    # Block 2: Execution (runner-aware execvpe)
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root

    # -- Block 1: Executable discovery ---------------------------------------------
    def find_executable(self, spec: ToolSpec) -> Path | None:
        """PATH win, then bin_home; internal tools fall back to runner candidates."""
        found = shutil.which(spec.binary)
        if found:
            return Path(found)
        local = bin_home() / spec.binary
        if local.exists() and os.access(local, os.X_OK):
            return local
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

    # -- Block 2: Execution ---------------------------------------------------------
    def run(self, spec: ToolSpec, args: list[str]) -> int:
        """Run the tool binary (or runner) with args; return 1 when not runnable.

        Subprocess-based execution (post-run reporting owned by the orchestrator).
        """
        exe = self.find_executable(spec)
        if exe is not None:
            tool_dir = self._root / spec.path
            if spec.category == "internal" and spec.runner == "cargo" and exe == tool_dir / "Cargo.toml":
                os.execvpe("cargo", ["cargo", "run", "--quiet", "--manifest-path",
                                     str(exe), "--bin", f"{spec.id}-arwaky-cli", *args], os.environ)
            elif spec.category == "internal" and spec.runner in {"uv", "python"} and exe == tool_dir:
                os.execvpe("uv", ["uv", "run", "--directory", str(tool_dir), spec.binary, *args], os.environ)
            elif spec.category == "internal" and spec.runner in {"uv", "python"} and exe == Path(spec.id):
                os.execvpe("python3", ["python3", "-m", spec.id, *args], os.environ)
            else:
                os.execvpe(str(exe), [str(exe), *args], os.environ)
        return 1
