"""FR-002 capability — execute a discovered tool (runner feature).

Launch is a plain subprocess exec of the discovered path; stdin/stdout/
stderr inherit the parent unless the tool is an MCP server (stdio then
managed per the MCP protocol). Daemons are invoked through their launcher,
never spawned ad hoc. Every failure path returns an int; nothing raises
out of `execute` into the CLI surface.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS
from modules.shared.src.taxonomy_paths_constant import REPO_ROOT as repo_root
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.shared.src.taxonomy_tool_vo import ToolSpec

#: Reserved non-zero exit code: "executable vanished between discovery and launch".
SENTINEL_EXECUTABLE_GONE = 126

#: Tool ids that are long-running daemons (container isolation invariant).
_DAEMON_IDS = frozenset({"9router", "anytype", "anytype-daemon"})


def _exec_command(spec: ToolSpec, executable: Path, args: list[str], root: Path) -> list[str]:
    """Build the argv for the subprocess exec (runner-aware, verbatim port)."""
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


class RunnerExecutor:
    """Launch a resolved executable and return the child's real exit code.

    # Block 1: Daemon routing (launcher, never ad hoc)
    # Block 2: Subprocess exec (stdio + exit-code fidelity)
    """

    # -- Block 1: Daemon routing -------------------------------------------------
    def _daemon_launcher(self, spec: ToolSpec, root: Path) -> Path | None:
        """Daemon tools must launch through their XDG bin launcher."""
        for name in ([spec.mcp_binary] if spec.is_mcp and spec.mcp_binary else []) + [spec.binary]:
            launcher = bin_home() / name
            if launcher.exists() and os.access(launcher, os.X_OK):
                return launcher.resolve()
        return None

    # -- Block 2: Subprocess exec ------------------------------------------------
    def execute(self, spec: ToolSpec, executable: Path, args: list[str], root: Path | None = None) -> int:
        """Launch *executable* with *args*; return the child's real exit code.

        - Missing executable at launch time -> SENTINEL_EXECUTABLE_GONE + message.
        - Broken/permission launch -> the child's code or the sentinel.
        - Long-running daemon -> returns once the start sequence completes.
        """
        base = root or repo_root
        if not executable.exists():
            print(f"Executable '{executable}' for tool '{spec.id}' vanished between discovery and launch (not installed).", file=sys.stderr)
            return SENTINEL_EXECUTABLE_GONE

        # Daemons: ensure launcher; a missing launcher is the vanished executable.
        if spec.id in _DAEMON_IDS:
            launcher = self._daemon_launcher(spec, base)
            if launcher is None:
                print(f"Daemon launcher for '{spec.id}' not found under {bin_home()}; start it via its service instead.", file=sys.stderr)
                return SENTINEL_EXECUTABLE_GONE

        # MCP servers manage their own stdio; plain tools inherit the parent.
        kwargs: dict = {}
        if spec.is_mcp:
            kwargs["stdin"] = subprocess.PIPE
            kwargs["stdout"] = subprocess.PIPE
            kwargs["stderr"] = subprocess.STDOUT

        try:
            argv = _exec_command(spec, executable, args, base)
            proc = subprocess.run(argv, check=False, **kwargs)
            return proc.returncode
        except (OSError, FileNotFoundError) as exc:
            print(f"Failed to launch '{spec.id}': {exc}", file=sys.stderr)
            return SENTINEL_EXECUTABLE_GONE
