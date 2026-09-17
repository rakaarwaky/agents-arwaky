"""Qwen-web updater (uv venv + Playwright, force) — port of tools/update/update_qwen_web.py.

Always pulls internal/qwen-web-arwaky, force-recreates the venv,
pip-reinstalls, reinstalls Playwright Chromium, re-creates per-role XDG
queues, and rewrites the launcher symlinks.
"""
from __future__ import annotations

import subprocess

from modules.shared.src.git.utility_git_update import update_submodule, write_install_stamp
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
from modules.shared.src.venv.capabilities_venv_installer import (
    ensure_venv,
    install_package,
    setup_bin_links,
)
from modules.shared.src.xdg.utility_xdg_paths import (
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


class QwenWebUpdater(IToolUpdater):
    """Force-reinstall internal/qwen-web-arwaky in a uv venv + Playwright."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def update(self, spec: ToolSpec) -> UpdateResult:
        root = self._root
        print(">>> Updating qwen-web-arwaky (XDG compliant)...")

        if not update_submodule(root, SRC_REL):
            return UpdateResult(False, spec.id, f"submodule update failed: {SRC_REL}")

        src_dir = root / SRC_REL
        if not src_dir.exists():
            return UpdateResult(False, spec.id, f"source not found {src_dir}")

        python_bin = ensure_venv(TOOL_NAME, force=True)
        install_package(python_bin, src_dir, TOOL_NAME)
        _install_playwright(python_bin)
        _setup_qwen_web_dirs()
        setup_bin_links(python_bin, LAUNCHERS)

        # D2: write provenance stamp for rollback/audit
        write_install_stamp(python_bin.parent.parent, TOOL_NAME, src_dir)

        print("\n>>> Successfully updated qwen-web-arwaky")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        return UpdateResult(
            True, spec.id,
            f"venv at {python_bin.parent}; data at {tool_data_dir(TOOL_NAME)}",
        )
