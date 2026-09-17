"""Workspace (google-workspace-mcp) installer (uv) — port of tools/install/install_workspace.py.

vendor/google-workspace-mcp is a Python package run via `uv run` (no venv copy).
Launchers `workspace-mcp` and `google-workspace-mcp` both point at the same entry.
"""
from __future__ import annotations

import subprocess

from modules.shared.src.launcher.capabilities_launcher_writer import write_uv_launchers
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import ensure_bin_home
from modules.shared.src.xdg.utility_xdg_paths import bin_home


SRC_REL = "vendor/google-workspace-mcp"
LAUNCHERS = [
    ("workspace-mcp", "workspace-mcp"),
    ("google-workspace-mcp", "workspace-mcp"),
]


class WorkspaceInstaller(IToolInstaller):
    """Install vendor/google-workspace-mcp via uv-run launchers."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if (bin_home() / "workspace-mcp").exists():
            return InstallResult(True, spec.id, "workspace is already installed")

        src_dir = root / SRC_REL
        if not src_dir.exists():
            subprocess.run(
                ["git", "-C", str(root), "submodule", "update", "--init", SRC_REL],
                check=False,
            )
        if not src_dir.exists():
            return InstallResult(False, spec.id, f"source not found {SRC_REL}")

        ensure_bin_home()
        created = write_uv_launchers(SRC_REL, LAUNCHERS, root=root)
        for p in created:
            print(f"  -> {p}")
        return InstallResult(True, spec.id, "google-workspace-mcp installed")
