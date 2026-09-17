"""Qwen-web-arwaky installer (uv venv + Playwright) — port of tools/install/install_qwen_web.py.

Creates a venv in ~/.local/share/qwen-web/venv/, pip-installs the
internal/qwen-web-arwaky package, installs Playwright Chromium, and symlinks
the launchers into ~/.local/bin/.
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
)
from modules.shared.src.xdg.utility_xdg_atomic_io import warn_if_bin_not_on_path
from modules.shared.src.xdg.utility_xdg_paths import (
    bin_home,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
)


TOOL_NAME = "qwen-web"
SRC_REL = f"internal/{TOOL_NAME}-arwaky"
LAUNCHERS = [
    ("qwen-web-arwaky", "qwen-web-arwaky"),
    ("qwa", "qwen-web-arwaky"),
    ("qwen-web-cli", "qwen-web-arwaky"),
    ("qwen-web-mcp", "qwen-web-mcp"),
    ("qwc", "qwen-web-arwaky"),
]


def _install_playwright(python_bin) -> None:
    print("  [install] Installing Playwright Chromium...")
    subprocess.run([str(python_bin), "-m", "playwright", "install", "chromium"], check=True)


def _setup_qwen_web_dirs() -> None:
    """qwen-web keeps per-role inbox queues and session state under XDG dirs."""
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


class QwenWebInstaller(IToolInstaller):
    """Install internal/qwen-web-arwaky via a uv-managed venv + Playwright."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if (bin_home() / "qwen-web-arwaky").exists():
            return InstallResult(True, spec.id, "qwen-web-arwaky is already installed")

        src_dir = root / SRC_REL
        if not src_dir.exists():
            subprocess.run(
                ["git", "-C", str(root), "submodule", "update", "--init", SRC_REL],
                check=False,
            )
        if not src_dir.exists():
            return InstallResult(False, spec.id, f"source not found {src_dir}")

        python_bin = ensure_venv(TOOL_NAME, force=False)
        install_package(python_bin, src_dir, TOOL_NAME)
        _install_playwright(python_bin)
        _setup_qwen_web_dirs()
        setup_bin_links(python_bin, LAUNCHERS)
        warn_if_bin_not_on_path()
        return InstallResult(True, spec.id, f"venv at {python_bin.parent}; data at {tool_data_dir(TOOL_NAME)}")
