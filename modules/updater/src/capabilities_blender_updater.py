"""Blender updater (uv venv, force) — port of tools/update/update_blender.py.

Always pulls the internal/lint-arwaky-style submodule (here
internal/blender-arwaky), then force-recreates the venv, pip-reinstalls the
package, and rewrites the launcher symlinks. No "already installed" skip.
"""
from __future__ import annotations

from modules.shared.src.git.utility_git_update import update_submodule, write_install_stamp
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
from modules.shared.src.venv.capabilities_venv_installer import (
    ensure_venv,
    install_package,
    setup_bin_links,
    setup_xdg_directories,
)
from modules.shared.src.xdg.utility_xdg_paths import tool_data_dir


TOOL_NAME = "blender-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
LAUNCHERS = [
    ("blender-arwaky", "blender-arwaky"),
    ("ba", "blender-arwaky"),
    ("blender-mcp", "blender-mcp"),
]


class BlenderUpdater(IToolUpdater):
    """Force-reinstall internal/blender-arwaky in a uv venv (XDG compliant)."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        print(">>> Updating blender-arwaky (XDG compliant)...")

        if not update_submodule(root, SRC_REL):
            return UpdateResult(False, spec.id, f"submodule update failed: {SRC_REL}")

        src_dir = root / SRC_REL
        if not src_dir.exists():
            return UpdateResult(False, spec.id, f"source not found {src_dir}")

        python_bin = ensure_venv(TOOL_NAME, force=True)
        install_package(python_bin, src_dir, TOOL_NAME)
        setup_xdg_directories(TOOL_NAME)
        setup_bin_links(python_bin, LAUNCHERS)

        # D2: write provenance stamp for rollback/audit
        write_install_stamp(python_bin.parent.parent, TOOL_NAME, src_dir)

        print("\n>>> Successfully updated blender-arwaky")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        return UpdateResult(
            True, spec.id,
            f"venv at {python_bin.parent}; data at {tool_data_dir(TOOL_NAME)}",
        )
