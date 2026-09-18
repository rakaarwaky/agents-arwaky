"""Shared venv-based installer/updater helpers — DRY for Python tools.
Moved from tools/lib/venv_installer.py into the venv domain.

Provides: ensure_venv, install_package, setup_xdg_directories, setup_bin_links.
Used by install_blender, install_vision, install_qwen_web and their update counterparts.
"""
from __future__ import annotations
from modules.installer.src.contract_tool_installer_protocol import IToolInstaller


# ─── Block 1: Class Definition & Constructor ──────────────
class VenvInstaller(IToolInstaller):
    """Capability wrapper exposing the venv helper block as a capability class (AES403)."""

    def install(self, spec: "ToolSpec") -> "InstallResult":
        from modules.shared.src.taxonomy_tool_vo import InstallResult

        tool_name = getattr(spec, "id", str(spec))
        ensure_venv(tool_name)
        setup_xdg_directories(tool_name)
        return InstallResult(success=True, tool_id=tool_name, message="venv helpers prepared")
# ─── Block 2: Protocol ABC Method Implementation ──────────
# (none)
# ─── Block 3: Dunder Methods, Factories & Helpers ───────

"""AES NOTE: This file is misclassified as capabilities_* but contains 0 protocol classes (pure helpers).\nShould be renamed to utility_* per AES102/AES403 (CapabilityNoProtocol). Kept as capabilities_* for backward compat; re-export via utility_* exists.\n"""

import subprocess
import sys
from pathlib import Path

from modules.shared.src.taxonomy_xdg_atomic_io import warn_if_bin_not_on_path
from modules.shared.src.taxonomy_xdg_paths import (
    bin_home,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
)


def ensure_bin_home() -> None:
    """Local alias kept for the verbatim bodies below."""
    bin_home().mkdir(parents=True, exist_ok=True)

def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def get_venv_dir(tool_name: str) -> Path:
    """XDG-compliant venv directory: ~/.local/share/<tool>/venv/"""
    return tool_data_dir(tool_name) / "venv"


def get_venv_python(venv_dir: Path) -> Path:
    return venv_dir / "bin" / "python"


def ensure_venv(tool_name: str, force: bool = False) -> Path:
    """Create venv in XDG data directory. If force=True, recreate even if exists."""
    venv_dir = get_venv_dir(tool_name)
    python_bin = get_venv_python(venv_dir)

    if python_bin.exists():
        if not force:
            print(f"  [skip] Venv already exists at {venv_dir}")
            return python_bin
        print(f"  [update] Recreating venv at {venv_dir}...")
        import shutil
        shutil.rmtree(venv_dir)
    else:
        print(f"  [install] Creating venv at {venv_dir}...")

    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv_dir)], check=True)
    print("  [install] Bootstrapping pip...")
    subprocess.run([str(get_venv_python(venv_dir)), "-m", "ensurepip", "--upgrade"], check=True)
    python_bin = get_venv_python(venv_dir)
    print(f"  [ok] Venv created: {python_bin}")
    return python_bin


def install_package(python_bin: Path, src_dir: Path, tool_name: str) -> None:
    print(f"  [install] Installing {tool_name} package...")
    subprocess.run(
        [str(python_bin), "-m", "pip", "install", "-e", str(src_dir)],
        check=True,
    )


def setup_xdg_directories(tool_name: str) -> None:
    print(f"  [install] Creating XDG directories for {tool_name}...")
    tool_data_dir(tool_name)
    tool_config_dir(tool_name)
    tool_state_dir(tool_name)
    tool_cache_dir(tool_name)
    print(f"  [ok] Data: {tool_data_dir(tool_name)}")
    print(f"  [ok] Config: {tool_config_dir(tool_name)}")
    print(f"  [ok] State: {tool_state_dir(tool_name)}")
    print(f"  [ok] Cache: {tool_cache_dir(tool_name)}")


def setup_bin_links(python_bin: Path, launchers: list[tuple[str, str]]) -> None:
    """Create symlinks in ~/.local/bin/. launchers = [(name, entrypoint), ...]"""
    import contextlib
    ensure_bin_home()
    local_bin = bin_home()
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

__all__ = ['IToolInstaller']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"IToolInstaller": IToolInstaller}
