"""Vision-arwaky installer (uv venv) — verbatim port of tools/install/install_vision.py.

Creates a venv in ~/.local/share/vision-arwaky/venv/, pip-installs the
internal/vision-arwaky package, and symlinks the launchers into ~/.local/bin/.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.installer.src.capabilities_venv_installer import (
    ensure_venv,
    install_package,
    setup_xdg_directories,
    setup_bin_links,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, tool_data_dir

ROOT = repo_root()

TOOL_NAME = "vision-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [
    ("vision-arwaky", "vision-arwaky-cli"),
    ("vision-arwaky-cli", "vision-arwaky-cli"),
    ("va", "vision-arwaky-cli"),
    ("vision-arwaky-mcp", "vision-arwaky-mcp"),
]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def is_installed() -> bool:
    return (bin_home() / "vision-arwaky").exists()


def _install_vision() -> int:
    if is_installed():
        print(">>> vision-arwaky is already installed. Use 'aa update vision' to reinstall.")
        return 0

    print(">>> Installing vision-arwaky (XDG compliant)...")

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

    print("\n>>> Successfully installed vision-arwaky")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    print(f"    Run 'vision-arwaky-cli init' to setup workspace symlinks")
    return 0


class VisionInstaller(IToolInstaller):
    """Install internal/vision-arwaky via a uv-managed venv (XDG compliant)."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def install(self, spec: ToolSpec) -> InstallResult:
        rc = _install_vision()
        return InstallResult(
            rc == 0,
            spec.id,
            "vision-arwaky installed" if rc == 0 else "vision-arwaky install failed",
        )
