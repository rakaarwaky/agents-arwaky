"""Blender-arwaky adapter (uv venv) — unified install + update + teardown.

Creates venv in ~/.local/share/blender-arwaky/venv/ and symlinks to
~/.local/bin/. Update rebuilds the venv in place and re-stamps the install.

Stateless leaf (AES404): module-level functions only, no classes.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import bin_home, tool_data_dir
from modules.tools.src.utility_tool_mechanics import ROOT, ensure_source, generic_owned
from modules.tools.src.utility_venv_helpers import (
    ensure_venv,
    install_package,
    setup_bin_links,
    setup_xdg_directories,
)

TOOL_NAME = "blender-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
LAUNCHERS = [("blender-arwaky", "blender-arwaky"), ("ba", "blender-arwaky"), ("blender-mcp", "blender-mcp")]


def satisfied(spec, root: Path | None = None) -> bool:
    return (bin_home() / "blender-arwaky").exists()


# -- install (from old installer adapter, verbatim mechanics) ----------------
def install(spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
    root = root or ROOT
    src_dir = root / SRC_REL

    if not ensure_source(root, SRC_REL):
        raise FileNotFoundError(f"source not found {src_dir}")

    python_bin = ensure_venv(TOOL_NAME, force=False)
    install_package(python_bin, src_dir, TOOL_NAME)
    setup_xdg_directories(TOOL_NAME)
    setup_bin_links(python_bin, LAUNCHERS)

    print("\n>>> Successfully installed blender-arwaky")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    print("    Run 'blender-arwaky init' to setup workspace symlinks")
    return [python_bin]


# -- update (from old updater adapter) ---------------------------------------
def is_pin_satisfied(spec, root: Path) -> tuple[bool, str]:
    source = root / SRC_REL
    if not source.exists():
        return False, "submodule not initialized"
    return False, "venv/pip (rebuild required)"


def update(spec, root: Path) -> list[Path]:
    from modules.shared.src.utility_git_update import (
        update_submodule,
        write_install_stamp,
    )

    print(f">>> Updating {TOOL_NAME} (XDG compliant)...")

    if not update_submodule(root, SRC_REL):
        raise ToolUpdateError(f"submodule update failed: {SRC_REL}")

    source = root / SRC_REL
    if not source.exists():
        raise ToolUpdateError(f"source not found {source}")

    python_bin = ensure_venv(TOOL_NAME, force=True)
    install_package(python_bin, source, TOOL_NAME)
    setup_xdg_directories(TOOL_NAME)
    setup_bin_links(python_bin, LAUNCHERS)
    write_install_stamp(python_bin.parent.parent, TOOL_NAME, source)

    created = [bin_home() / name for name, _entry in LAUNCHERS]
    print(f"\n>>> Successfully updated {TOOL_NAME}")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    return created


# -- teardown data --------------------------------------------------------------
def owned_paths(spec, root: Path | None = None) -> list[Path]:
    return generic_owned(spec, [name for name, _e in LAUNCHERS])
