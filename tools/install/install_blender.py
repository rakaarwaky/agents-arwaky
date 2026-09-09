#!/usr/bin/env python3
"""Installer blender — blender-arwaky (Python, XDG compliant).

Creates venv in ~/.local/share/blender-arwaky/venv/ and symlinks to ~/.local/bin/.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from paths import repo_root
ROOT = repo_root()

from xdg import bin_home, tool_data_dir
from venv_installer import ensure_venv, install_package, setup_xdg_directories, setup_bin_links

TOOL_NAME = "blender-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [("blender-arwaky", "blender-arwaky"), ("ba", "blender-arwaky"), ("blender-mcp", "blender-mcp")]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def is_installed() -> bool:
    return (bin_home() / "blender-arwaky").exists()


def main() -> int:
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


if __name__ == "__main__":
    raise SystemExit(main())
