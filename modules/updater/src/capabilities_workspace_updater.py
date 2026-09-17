"""Workspace (google-workspace-mcp) updater (uv) — port of tools/update/update_workspace.py.

Always pulls vendor/google-workspace-mcp and rewrites the uv-run launchers.
"""
from __future__ import annotations

from modules.shared.src.git.utility_git_update import update_submodule
from modules.shared.src.launcher.capabilities_launcher_writer import write_uv_launchers
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
from modules.shared.src.xdg.utility_xdg_atomic_io import ensure_bin_home


SRC_REL = "vendor/google-workspace-mcp"
LAUNCHERS = [
    ("workspace-mcp", "workspace-mcp"),
    ("google-workspace-mcp", "workspace-mcp"),
]


class WorkspaceUpdater(IToolUpdater):
    """Update vendor/google-workspace-mcp (uv-run launchers rewritten)."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        print(">>> Updating google-workspace-mcp (XDG compliant)...")

        if not update_submodule(root, SRC_REL):
            return UpdateResult(False, spec.id, f"submodule update failed: {SRC_REL}")

        src_dir = root / SRC_REL
        if not src_dir.exists():
            return UpdateResult(False, spec.id, f"source not found {src_dir}")

        ensure_bin_home()
        created = write_uv_launchers(SRC_REL, LAUNCHERS, root=root)
        for p in created:
            print(f"  -> {p}")
        print(">>> Successfully updated google-workspace-mcp")
        return UpdateResult(True, spec.id, "google-workspace-mcp updated (launchers rewritten)")
