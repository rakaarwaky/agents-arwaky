"""Workspace (google-workspace-mcp) adapter (uv) — verbatim port of tools/install/install_workspace.py.

vendor/google-workspace-mcp is a Python package run via `uv run` (no venv copy).
Launchers `workspace-mcp` and `google-workspace-mcp` both point at the same entry.
"""
from __future__ import annotations

from pathlib import Path

from modules.installer.src.utility_adapter_base import AdapterBase, ROOT
from modules.installer.src.utility_launcher_writer import write_uv_launchers

SRC_REL = "vendor/google-workspace-mcp"
LAUNCHERS = [
    ("workspace-mcp", "workspace-mcp"),
    ("google-workspace-mcp", "workspace-mcp"),
]


class WorkspaceAdapter(AdapterBase):
    """Install vendor/google-workspace-mcp via uv-run launchers."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        from modules.shared.src.taxonomy_xdg_paths import bin_home
        return (bin_home() / "workspace-mcp").exists()

    def install(self, spec: ToolSpec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        src_dir = root / SRC_REL

        if not self.ensure_source(root, SRC_REL):
            raise FileNotFoundError(f"source not found {src_dir}")

        created = write_uv_launchers(SRC_REL, LAUNCHERS[:1], root=root)
        for p in created:
            print(f"  -> {p}")
        # google-workspace-mcp is a PATH alias for workspace-mcp.
        from modules.installer.src.utility_launcher_writer import symlink_alias
        alias = symlink_alias(LAUNCHERS[1][0], created[0])
        print(f"  -> {alias}")
        created.append(alias)
        print(">>> Successfully installed google-workspace-mcp")
        return created
