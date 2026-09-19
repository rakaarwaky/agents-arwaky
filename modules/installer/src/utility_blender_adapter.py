"""Blender-arwaky adapter (uv venv) — verbatim port of tools/install/install_blender.py.

Creates venv in ~/.local/share/blender-arwaky/venv/ and symlinks to ~/.local/bin/.
"""
from __future__ import annotations

from pathlib import Path

from modules.installer.src.utility_adapter_base import AdapterBase, ROOT
from modules.installer.src.utility_venv_helpers import (
    ensure_venv,
    install_package,
    setup_xdg_directories,
    setup_bin_links,
)

TOOL_NAME = "blender-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
LAUNCHERS = [("blender-arwaky", "blender-arwaky"), ("ba", "blender-arwaky"), ("blender-mcp", "blender-mcp")]


class BlenderAdapter(AdapterBase):
    """Install internal/blender-arwaky via a uv-managed venv (XDG compliant)."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        from modules.shared.src.taxonomy_xdg_paths import bin_home
        return (bin_home() / "blender-arwaky").exists()

    def install(self, spec: ToolSpec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        from modules.shared.src.taxonomy_xdg_paths import tool_data_dir

        root = root or ROOT
        src_dir = root / SRC_REL

        if not self.ensure_source(root, SRC_REL):
            raise FileNotFoundError(f"source not found {src_dir}")

        python_bin = ensure_venv(TOOL_NAME, force=False)
        install_package(python_bin, src_dir, TOOL_NAME)
        setup_xdg_directories(TOOL_NAME)
        setup_bin_links(python_bin, LAUNCHERS)

        print("\n>>> Successfully installed blender-arwaky")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        print(f"    Run 'blender-arwaky init' to setup workspace symlinks")
        return [python_bin]
