"""FR-004 action — run a tool: discover its executable, then exec it.

Sub-steps (internal, not separate public methods):
1. Discover: universal deterministic order, identical for every tool —
   XDG bin launcher -> host PATH -> per-tool install dir. MCP tools
   resolve through ``mcp_binary`` first. Read-only: never mutates install
   state and never invokes a package manager. Symlinked launchers are
   resolved to their target. No candidate found -> ``run`` returns 1
   without reaching execution.
2. Execute: a plain subprocess exec of the discovered path with the
   forwarded args; stdin/stdout/stderr inherit the parent unless the
   tool is an MCP server (stdio then managed per the MCP protocol).
   Daemons are invoked through their launcher, never spawned ad hoc.

Every failure path returns an int; nothing raises out of ``run``.
Sentinel 126 (``SENTINEL_EXECUTABLE_GONE``) is reserved for "executable
vanished between discovery and launch".
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.contract_tools_protocol import IToolRunProtocol
from modules.shared.src.taxonomy_common_constant import REPO_ROOT as repo_root
from modules.shared.src.taxonomy_common_constant import TOOL_RUNNERS
from modules.shared.src.taxonomy_common_vo import ToolSpec, bin_home
from modules.shared.src.taxonomy_tools_constant import (
    DAEMON_TOOL_IDS,
    SENTINEL_EXECUTABLE_GONE,
)
from modules.shared.src.taxonomy_tools_vo import ExitCode


def _exec_command(spec: ToolSpec, executable: Path, args: list[str], root: Path) -> list[str]:
    """Build the argv for the subprocess exec (runner-aware, exact port)."""
    tool_dir = root / spec.path
    runner = spec.runner or TOOL_RUNNERS.get(spec.id, "")
    names = [spec.mcp_binary, spec.binary] if spec.is_mcp and spec.mcp_binary else [spec.binary]

    if spec.category == "internal" and runner == "cargo" and executable == tool_dir / "Cargo.toml":
        return ["cargo", "run", "--quiet", "--manifest-path", str(executable),
                "--bin", f"{spec.id}-arwaky-cli", "--", *args]
    if spec.category == "internal" and runner in ("uv", "python") and executable == tool_dir:
        if shutil.which("uv"):
            return ["uv", "run", "--directory", str(tool_dir), spec.binary, *args]
        if shutil.which("python3"):
            return ["python3", "-m", spec.id, *args]
    if spec.category == "internal" and executable == Path(spec.id):
        return [sys.executable, "-m", spec.id, *args]
    if spec.category == "internal" and runner in ("uv", "python") and executable.name in names:
        return [str(executable), *args]
    return [str(executable), *args]


# ─── Block 1: Class Definition & Constructor ─────────────────────────
class RunnerCapability(IToolRunProtocol):
    """Business action run(spec, args, root): discover + exec, return exit code."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root

    # ─── Block 2: Public Contract (domain protocol ONLY) ─────────────
    def run(self, spec: ToolSpec, args: list[str], root: Path | None = None) -> ExitCode:
        # Sub-step 1: discover the concrete launch path; None -> return 1.
        base = root or self._root or repo_root
        exe = self._discover(spec, base)
        if exe is None:
            return ExitCode(1)

        # Sub-step 2: launch and return the child's real exit code.
        return ExitCode(self._execute(spec, exe, args, base))

    def discover(self, spec: ToolSpec, root: Path | None = None) -> Path | None:
        """Public discovery: first valid candidate, resolved; None when absent.

        Read-only: never mutates install state. Used by the agent aggregate
        for `executable_path` / `find_executable` without reaching execution.
        """
        base = root or self._root or repo_root
        return self._discover(spec, base)

    def execute(self, spec: ToolSpec, executable: Path, args: list[str], root: Path | None = None) -> int:
        """Public execution of a resolved *executable*; the child's exit code."""
        base = root or self._root or repo_root
        return self._execute(spec, executable, args, base)

    # ─── Block 3: Dunder Methods, Factories & Helpers ────────────────
    def _discover(self, spec: ToolSpec, root: Path) -> Path | None:
        """First valid candidate in discovery order, resolved; None when absent."""
        for candidate in self._candidates(spec, root):
            if candidate.exists() and os.access(candidate, os.X_OK):
                return candidate
            if candidate.suffix == ".toml" or candidate.name in (spec.id,):
                # Runner candidates are not directly executable; accept them as-is.
                return candidate
        return None

    @staticmethod
    def _names(spec: ToolSpec) -> list[str]:
        """Executable names to probe: mcp_binary (MCP tools) first, then binary."""
        names: list[str] = []
        if spec.is_mcp and spec.mcp_binary:
            names.append(spec.mcp_binary)
        names.append(spec.binary)
        return names

    def _candidates(self, spec: ToolSpec, root: Path) -> list[Path]:
        """Ordered candidate paths: XDG bin launcher -> PATH -> install dir."""
        candidates: list[Path] = []
        for name in self._names(spec):
            # 1. XDG bin launcher (installer-registered, found even before the binary).
            launcher = bin_home() / name
            if launcher.exists() and os.access(launcher, os.X_OK):
                candidates.append(launcher.resolve())

            # 2. Host PATH.
            found = shutil.which(name)
            if found:
                p = Path(found)
                if p not in candidates:
                    candidates.append(p)

        # 3. Per-tool install dir (internal tools: runner candidates).
        if spec.category == "internal" and spec.path:
            tool_dir = root / spec.path
            runner = spec.runner or TOOL_RUNNERS.get(spec.id, "")
            if runner == "cargo" and shutil.which("cargo") and (tool_dir / "Cargo.toml").exists():
                candidates.append(tool_dir / "Cargo.toml")
            if runner in ("uv", "python") and tool_dir.exists():
                if shutil.which("uv"):
                    candidates.append(tool_dir)
                elif shutil.which("python3"):
                    candidates.append(Path(spec.id))
        return candidates

    def _execute(
        self,
        spec: ToolSpec,
        executable: Path,
        args: list[str],
        root: Path | None = None,
    ) -> int:
        """Launch *executable* with *args*; return the child's real exit code.

        - Missing executable at launch time -> SENTINEL_EXECUTABLE_GONE + message.
        - Broken/permission launch -> the child's code or the sentinel.
        - Long-running daemon -> returns once the start sequence completes.
        """
        base = root or self._root or repo_root
        if not executable.exists():
            print(f"Executable '{executable}' for tool '{spec.id}' vanished between discovery and launch (not installed).", file=sys.stderr)
            return SENTINEL_EXECUTABLE_GONE

        # Daemons: ensure launcher; a missing launcher is the vanished executable.
        if spec.id in DAEMON_TOOL_IDS:
            launcher = self._daemon_launcher(spec, base)
            if launcher is None:
                print(f"Daemon launcher for '{spec.id}' not found under {bin_home()}; start it via its service instead.", file=sys.stderr)
                return SENTINEL_EXECUTABLE_GONE

        # P0-4: inherit parent stdio for all tools.
        # Capturing an MCP server's pipes with subprocess.run deadlocks
        # (the server keeps stdio open indefinitely and its output is never
        # forwarded to the caller); MCP harnesses spawn their own servers —
        # `aa tool run` is interactive use.
        try:
            argv = _exec_command(spec, executable, args, base)
            proc = subprocess.run(argv, check=False)
            return proc.returncode
        except (OSError, FileNotFoundError) as exc:
            print(f"Failed to launch '{spec.id}': {exc}", file=sys.stderr)
            return SENTINEL_EXECUTABLE_GONE

    def _daemon_launcher(self, spec: ToolSpec, root: Path) -> Path | None:
        """Daemon tools must launch through their XDG bin launcher."""
        for name in ([spec.mcp_binary] if spec.is_mcp and spec.mcp_binary else []) + [spec.binary]:
            launcher = bin_home() / name
            if launcher.exists() and os.access(launcher, os.X_OK):
                return launcher.resolve()
        return None


__all__ = ["RunnerCapability"]
