"""Qwen-web-arwaky installer (uv venv + Playwright) — verbatim port of tools/install/install_qwen_web.py.

Creates a venv in ~/.local/share/qwen-web/venv/, pip-installs the
internal/qwen-web-arwaky package, installs Playwright Chromium, and symlinks
the launchers into ~/.local/bin/.
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
    setup_bin_links,
)
from modules.shared.src.xdg.utility_xdg_paths import (
    bin_home,
    tool_data_dir,
    tool_config_dir,
    tool_state_dir,
    tool_cache_dir,
)

ROOT = repo_root()

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


def install_playwright(python_bin: Path) -> None:
    print("  [install] Installing Playwright Chromium...")
    subprocess.run([str(python_bin), "-m", "playwright", "install", "chromium"], check=True)


def setup_qwen_web_dirs() -> None:
    print("  [install] Creating XDG directories...")
    data_dir = tool_data_dir(TOOL_NAME)
    config_dir = tool_config_dir(TOOL_NAME)
    state_dir = tool_state_dir(TOOL_NAME)
    cache_dir = tool_cache_dir(TOOL_NAME)
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


def is_installed() -> bool:
    return (bin_home() / "qwen-web-arwaky").exists()


def _install_qwen_web() -> int:
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

    python_bin = ensure_venv(TOOL_NAME, force=False)
    install_package(python_bin, SRC_DIR, TOOL_NAME)
    install_playwright(python_bin)
    setup_qwen_web_dirs()
    setup_bin_links(python_bin, LAUNCHERS)

    print("\n>>> Successfully installed qwen-web-arwaky")
    print(f"    Venv: {python_bin.parent}")
    print(f"    Data: {tool_data_dir(TOOL_NAME)}")
    print(f"    Run 'qwc init' to setup workspace symlinks")
    return 0


class QwenWebInstaller(IToolInstaller):
    """Install internal/qwen-web-arwaky via a uv-managed venv + Playwright."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def install(self, spec: ToolSpec) -> InstallResult:
        rc = _install_qwen_web()
        return InstallResult(
            rc == 0,
            spec.id,
            "qwen-web-arwaky installed" if rc == 0 else "qwen-web-arwaky install failed",
        )
