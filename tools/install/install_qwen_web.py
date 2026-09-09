#!/usr/bin/env python3
"""Installer qwen-web — qwen-web-arwaky (Python, XDG compliant).

Creates venv in ~/.local/share/qwen-web/venv/ and symlinks to ~/.local/bin/.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (
    bin_home,
    ensure_bin_home,
    tool_data_dir,
    tool_config_dir,
    tool_state_dir,
    tool_cache_dir,
    warn_if_bin_not_on_path,
)

TOOL_NAME = "qwen-web"
SRC_REL = f"internal/{TOOL_NAME}-arwaky"
SRC_DIR = ROOT / SRC_REL

LAUNCHERS = [
    ("qwen-web-arwaky", "qwen-web-arwaky"),
    ("qwa", "qwen-web-arwaky"),
    ("qwen-web-cli", "qwen-web-arwaky"),
    ("qwen-web-mcp", "qwen-web-mcp"),
    ("qwc", "qwen-web-arwaky"),
]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def get_venv_dir() -> Path:
    """Get XDG-compliant venv directory: ~/.local/share/qwen-web/venv/"""
    return tool_data_dir(TOOL_NAME) / "venv"


def get_venv_python(venv_dir: Path) -> Path:
    """Get python binary path inside venv."""
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def ensure_venv() -> Path:
    """Create venv in XDG data directory if not exists."""
    venv_dir = get_venv_dir()
    python_bin = get_venv_python(venv_dir)

    if python_bin.exists():
        print(f"  [skip] Venv already exists at {venv_dir}")
        return python_bin

    print(f"  [install] Creating venv at {venv_dir}...")
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv_dir)], check=True)

    # Bootstrap pip using get-pip.py
    print("  [install] Bootstrapping pip...")
    subprocess.run(
        [str(python_bin), "-m", "ensurepip", "--upgrade"],
        check=True,
    )

    python_bin = get_venv_python(venv_dir)
    print(f"  [ok] Venv created: {python_bin}")
    return python_bin





def install_package(python_bin: Path) -> None:
    """Install qwen-web package in editable mode."""
    print("  [install] Installing qwen-web package...")
    subprocess.run(
        [str(python_bin), "-m", "pip", "install", "-e", str(SRC_DIR)],
        check=True,
    )


def install_playwright(python_bin: Path) -> None:
    """Install Playwright Chromium browser."""
    print("  [install] Installing Playwright Chromium...")
    subprocess.run(
        [str(python_bin), "-m", "playwright", "install", "chromium"],
        check=True,
    )


def setup_xdg_directories() -> None:
    """Create XDG directories for qwen-web."""
    print("  [install] Creating XDG directories...")

    # Create main directories
    data_dir = tool_data_dir(TOOL_NAME)
    config_dir = tool_config_dir(TOOL_NAME)
    state_dir = tool_state_dir(TOOL_NAME)
    cache_dir = tool_cache_dir(TOOL_NAME)

    # Create subdirectories
    for role in ("role-architect", "role-business-analyst", "role-tech-lead"):
        (data_dir / "input" / role / "done").mkdir(parents=True, exist_ok=True)
        (data_dir / "input" / role / "failed").mkdir(parents=True, exist_ok=True)

    (data_dir / "output").mkdir(parents=True, exist_ok=True)
    (data_dir / "qwen_session").mkdir(parents=True, exist_ok=True)
    (state_dir / "log").mkdir(parents=True, exist_ok=True)
    (cache_dir / ".processing").mkdir(parents=True, exist_ok=True)

    print(f"  [ok] Data: {data_dir}")
    print(f"  [ok] Config: {config_dir}")
    print(f"  [ok] State: {state_dir}")
    print(f"  [ok] Cache: {cache_dir}")


def setup_bin_links(python_bin: Path) -> None:
    """Create symlinks in ~/.local/bin/ pointing to venv executables."""
    if sys.platform == "win32":
        return

    ensure_bin_home()
    local_bin = bin_home()
    venv_bin_dir = python_bin.parent

    print(f"  [install] Creating launchers in {local_bin}...")

    for name in ("qwen-web-arwaky", "qwa", "qwen-web-cli", "qwc", "qwen-web-mcp"):
        src = venv_bin_dir / name
        dst = local_bin / name
        if src.exists():
            if dst.is_symlink() or dst.exists():
                with __import__("contextlib").suppress(OSError):
                    dst.unlink()
            with __import__("contextlib").suppress(OSError):
                dst.symlink_to(src)
                print(f"  [ok] {dst} -> {src}")

    warn_if_bin_not_on_path()


def is_installed() -> bool:
    """Check if qwen-web-arwaky is already installed (binary exists)."""
    return (bin_home() / "qwen-web-arwaky").exists()


def main() -> int:
    if is_installed():
        print(">>> qwen-web-arwaky is already installed. Use 'aa update qwen-web' to reinstall.")
        return 0

    print(">>> Installing qwen-web-arwaky (XDG compliant)...")

    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_REL}...")
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", SRC_REL])

    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    # 1. Create venv in XDG data directory
    python_bin = ensure_venv()

    # 2. Install package
    install_package(python_bin)

    # 3. Install playwright
    install_playwright(python_bin)

    # 4. Create XDG directories
    setup_xdg_directories()

    # 5. Create launchers
    setup_bin_links(python_bin)

    print("\n>>> Successfully installed qwen-web-arwaky")
    print(f"    Venv: {get_venv_dir()}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    print(f"    Run 'qwc init' to setup workspace symlinks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
