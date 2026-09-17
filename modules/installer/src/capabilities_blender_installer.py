"""Blender-arwaky installer (uv venv) — verbatim port of tools/install/install_blender.py.

Creates venv in ~/.local/share/blender-arwaky/venv/ and symlinks to ~/.local/bin/.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.venv.capabilities_venv_installer import (
    ensure_venv,
    install_package,
    setup_xdg_directories,
    setup_bin_links,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, tool_data_dir

ROOT = repo_root()

TOOL_NAME = "blender-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [("blender-arwaky", "blender-arwaky"), ("ba", "blender-arwaky"), ("blender-mcp", "blender-mcp")]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def is_installed() -> bool:
    return (bin_home() / "blender-arwaky").exists()


def _install_blender() -> int:
    if is_installed():
        print(">>> blender-arwaky is already installed. Use 'aa update blender' to reinstall.")
        return 0

    print(">>> Installing blender-arwaky (XDG compliant)...")

    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_REL}...")
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", SRC_REL])

    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    python_bin = ensure_venv(TOOL_NAME, force=False)
    install_package(python_bin, SRC_DIR, TOOL_NAME)
    setup_xdg_directories(TOOL_NAME)
    setup_bin_links(python_bin, LAUNCHERS)

    print("\n>>> Successfully installed blender-arwaky")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    print(f"    Run 'blender-arwaky init' to setup workspace symlinks")
    return 0


class BlenderInstaller(IToolInstaller):
    """Install internal/blender-arwaky via a uv-managed venv (XDG compliant)."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def install(self, spec: ToolSpec) -> InstallResult:
        rc = _install_blender()
        return InstallResult(
            rc == 0,
            spec.id,
            "blender-arwaky installed" if rc == 0 else "blender-arwaky install failed",
        )
