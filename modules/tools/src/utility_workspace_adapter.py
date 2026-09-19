"""Workspace (google-workspace-mcp) adapter (uv) — unified install + update + teardown.

vendor/google-workspace-mcp is a Python package run via `uv run` (no venv copy).
Launchers `workspace-mcp` and `google-workspace-mcp` both point at the same entry.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.tools.src.utility_adapter_base import AdapterBase, ROOT
from modules.tools.src.utility_launcher_writer import symlink_alias, write_uv_launchers

SRC_REL = "vendor/google-workspace-mcp"
LAUNCHERS = [
    ("workspace-mcp", "workspace-mcp"),
    ("google-workspace-mcp", "workspace-mcp"),
]


class WorkspaceAdapter(AdapterBase):
    """Install/update vendor/google-workspace-mcp via uv-run launchers."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        from modules.shared.src.taxonomy_xdg_paths import bin_home
        return (bin_home() / "workspace-mcp").exists()

    def _write_launchers(self, root: Path) -> list[Path]:
        created = write_uv_launchers(SRC_REL, LAUNCHERS[:1], root=root)
        for p in created:
            print(f"  -> {p}")
        # google-workspace-mcp is a PATH alias for workspace-mcp.
        alias = symlink_alias(LAUNCHERS[1][0], created[0])
        print(f"  -> {alias}")
        created.append(alias)
        return created

    # -- install (from old installer adapter, verbatim mechanics) ----------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        src_dir = root / SRC_REL

        if not self.ensure_source(root, SRC_REL):
            raise FileNotFoundError(f"source not found {src_dir}")

        created = self._write_launchers(root)
        print(">>> Successfully installed google-workspace-mcp")
        return created

    # -- update (from old updater adapter) ---------------------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        source = root / SRC_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "uv project (rebuild required)"

    def update(self, spec, root: Path) -> list[Path]:
        from modules.shared.src.utility_git_update import update_submodule

        source = root / SRC_REL
        if not update_submodule(root, SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
        if not source.exists():
            raise ToolUpdateError(f"source not found {source}")

        created = self._write_launchers(root)
        print(">>> Successfully updated google-workspace-mcp")
        return created

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        return self.generic_owned(spec, ["workspace-mcp", "google-workspace-mcp"])
