"""Blender-arwaky installer (uv venv) — port of tools/install/install_blender.py.

Creates a venv in ~/.local/share/blender-arwaky/venv/, pip-installs the
internal/blender-arwaky package, and symlinks the launchers into ~/.local/bin/.
"""
from __future__ import annotations

import subprocess
import sys

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.venv.capabilities_venv_installer import (
    ensure_venv,
    install_package,
    setup_bin_links,
    setup_xdg_directories,
)
from modules.shared.src.xdg.utility_xdg_paths import bin_home, tool_data_dir


TOOL_NAME = "blender-arwaky"
LAUNCHERS = [
    ("blender-arwaky", "blender-arwaky"),
    ("ba", "blender-arwaky"),
    ("blender-mcp", "blender-mcp"),
]


class BlenderInstaller(IToolInstaller):
    """Install internal/blender-arwaky via a uv-managed venv (XDG compliant)."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if (bin_home() / "blender-arwaky").exists():
            return InstallResult(True, spec.id, "blender-arwaky is already installed")

        src_rel = f"internal/{TOOL_NAME}"
        src_dir = root / src_rel
        if not src_dir.exists():
            subprocess.run(
                ["git", "-C", str(root), "submodule", "update", "--init", src_rel],
                check=False,
            )
        if not src_dir.exists():
            return InstallResult(False, spec.id, f"source not found {src_dir}")

        python_bin = ensure_venv(TOOL_NAME, force=False)
        install_package(python_bin, src_dir, TOOL_NAME)
        setup_xdg_directories(TOOL_NAME)
        setup_bin_links(python_bin, LAUNCHERS)
        return InstallResult(
            True,
            spec.id,
            f"venv at {python_bin.parent}; data at {tool_data_dir(TOOL_NAME)}",
        )
