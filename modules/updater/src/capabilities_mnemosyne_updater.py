"""Mnemosyne updater (uv) — port of tools/update/update_mnemosyne.py.

Always pulls vendor/mnemosyne and rewrites the uv-run launchers. The MCP
stdio server needs the [mcp] optional-dependency group, so the launchers
carry `uv_args=["--extra", "mcp"]` — kept in sync with the installer.
"""
from __future__ import annotations

from modules.shared.src.git.utility_git_update import update_submodule
from modules.shared.src.launcher.capabilities_launcher_writer import write_uv_launchers
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
from modules.shared.src.xdg.utility_xdg_atomic_io import ensure_bin_home


SRC_REL = "vendor/mnemosyne"
LAUNCHERS = [
    ("mnemosyne", "mnemosyne"),
    ("mnemosyne-mcp", "mnemosyne"),
]
# Keep in sync with capabilities_mnemosyne_updater.py's installer counterpart:
# the MCP stdio server needs the [mcp] optional-dependency group in the uv runtime.
UV_ARGS = ["--extra", "mcp"]


class MnemosyneUpdater(IToolUpdater):
    """Update vendor/mnemosyne (uv-run launchers with the [mcp] extra)."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        print(">>> Updating mnemosyne (XDG compliant)...")

        if not update_submodule(root, SRC_REL):
            return UpdateResult(False, spec.id, f"submodule update failed: {SRC_REL}")

        src_dir = root / SRC_REL
        if not src_dir.exists():
            return UpdateResult(False, spec.id, f"source not found {src_dir}")

        ensure_bin_home()
        created = write_uv_launchers(SRC_REL, LAUNCHERS, root=root, uv_args=UV_ARGS)
        for p in created:
            print(f"  -> {p}")
        print(">>> Successfully updated mnemosyne")
        return UpdateResult(True, spec.id, "mnemosyne updated (launchers rewritten)")
