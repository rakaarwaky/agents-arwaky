"""Blender updater adapter — leaf utility for one manifest tool.

Mirrors the original tools/update/update_blender.py mechanics: submodule
bump, venv rebuild, pip install, bin links, install stamp.
"""
from __future__ import annotations

import contextlib
import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import warn_if_bin_not_on_path
from modules.shared.src.taxonomy_xdg_paths import (
    bin_home,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
)
from modules.shared.src.utility_git_update import update_submodule, write_install_stamp
from modules.shared.src.taxonomy_tool_vo import ToolSpec

TOOL_NAME = "blender-arwaky"
SRC_REL = f"internal/{TOOL_NAME}"
LAUNCHERS = [
    ("blender-arwaky", "blender-arwaky"),
    ("ba", "blender-arwaky"),
    ("blender-mcp", "blender-mcp"),
]


def _ensure_venv(tool_name: str, force: bool = False) -> Path:
    """venv bootstrap in the XDG data dir (leaf helper, no cross-feature imports)."""
    venv_dir = tool_data_dir(tool_name) / "venv"
    python_bin = venv_dir / "bin" / "python"
    if python_bin.exists():
        if not force:
            print(f"  [skip] Venv already exists at {venv_dir}")
            return python_bin
        print(f"  [update] Recreating venv at {venv_dir}...")
        shutil.rmtree(venv_dir)
    else:
        print(f"  [install] Creating venv at {venv_dir}...")
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv_dir)], check=True)
    print("  [install] Bootstrapping pip...")
    subprocess.run([str(venv_dir / "bin" / "python"), "-m", "ensurepip", "--upgrade"], check=True)
    python_bin = venv_dir / "bin" / "python"
    print(f"  [ok] Venv created: {python_bin}")
    return python_bin


def _install_package(python_bin: Path, src_dir: Path, tool_name: str) -> None:
    print(f"  [install] Installing {tool_name} package...")
    subprocess.run([str(python_bin), "-m", "pip", "install", "-e", str(src_dir)], check=True)


def _setup_xdg_directories(tool_name: str) -> None:
    print(f"  [install] Creating XDG directories for {tool_name}...")
    for directory in (
        tool_data_dir(tool_name),
        tool_config_dir(tool_name),
        tool_state_dir(tool_name),
        tool_cache_dir(tool_name),
    ):
        directory.mkdir(parents=True, exist_ok=True)
    print(f"  [ok] Data: {tool_data_dir(tool_name)}")


def _setup_bin_links(python_bin: Path, launchers: list[tuple[str, str]]) -> None:
    """Symlink venv bin entries into XDG bin (leaf helper, no cross-feature imports)."""
    local_bin = bin_home()
    local_bin.mkdir(parents=True, exist_ok=True)
    venv_bin_dir = python_bin.parent
    print(f"  [install] Creating launchers in {local_bin}...")
    for name, _entry in launchers:
        src = venv_bin_dir / name
        dst = local_bin / name
        if src.exists():
            if dst.is_symlink() or dst.exists():
                with contextlib.suppress(OSError):
                    dst.unlink()
            with contextlib.suppress(OSError):
                dst.symlink_to(src)
                print(f"  [ok] {dst} -> {src}")
    warn_if_bin_not_on_path()


class BlenderUpdaterAdapter:
    """Blender (venv/pip) update sequence."""

    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        source = root / SRC_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "venv/pip (rebuild required)"

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        print(f">>> Updating {TOOL_NAME} (XDG compliant)...")

        if not update_submodule(root, SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {SRC_REL}")

        source = root / SRC_REL
        if not source.exists():
            raise ToolUpdateError(f"source not found {source}")

        python_bin = _ensure_venv(TOOL_NAME, force=True)
        _install_package(python_bin, source, TOOL_NAME)
        _setup_xdg_directories(TOOL_NAME)
        _setup_bin_links(python_bin, LAUNCHERS)

        write_install_stamp(python_bin.parent.parent, TOOL_NAME, source)

        created = [bin_home() / name for name, _entry in LAUNCHERS]
        print(f"\n>>> Successfully updated {TOOL_NAME}")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        return created
