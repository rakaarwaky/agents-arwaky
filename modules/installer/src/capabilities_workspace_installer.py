"""Workspace (google-workspace-mcp) installer (uv) — verbatim port of tools/install/install_workspace.py.

vendor/google-workspace-mcp is a Python package run via `uv run` (no venv copy).
Launchers `workspace-mcp` and `google-workspace-mcp` both point at the same entry.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.installer.src.contract_tool_installer import IToolInstaller
from modules.installer.src.utility_launcher_writer import write_uv_launchers
from modules.shared.src.utility_xdg_atomic_io import ensure_bin_home
from modules.shared.src.utility_xdg_paths import bin_home

ROOT = repo_root()

SRC_REL = "vendor/google-workspace-mcp"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [
    ("workspace-mcp", "workspace-mcp"),
    ("google-workspace-mcp", "workspace-mcp"),
]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def is_installed() -> bool:
    """Check if workspace-mcp is already installed (binary exists)."""
    return (bin_home() / "workspace-mcp").exists()


def _install_workspace() -> int:
    if is_installed():
        print(">>> workspace is already installed. Use 'aa update workspace' to reinstall.")
        return 0

    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_REL}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", SRC_REL])
    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    ensure_bin_home()
    created = write_uv_launchers(SRC_REL, LAUNCHERS, root=ROOT)
    for p in created:
        print(f"  -> {p}")
    print(">>> Successfully installed google-workspace-mcp")
    return 0


class WorkspaceInstaller(IToolInstaller):
    """Install vendor/google-workspace-mcp via uv-run launchers."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def install(self, spec: ToolSpec) -> InstallResult:
        rc = _install_workspace()
        return InstallResult(
            rc == 0,
            spec.id,
            "google-workspace-mcp installed" if rc == 0 else "google-workspace-mcp install failed",
        )
