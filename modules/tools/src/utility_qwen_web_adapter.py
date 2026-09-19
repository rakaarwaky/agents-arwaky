"""Qwen-web-arwaky adapter (uv venv + Playwright) — unified install + update + teardown.

Creates a venv in ~/.local/share/qwen-web/venv/, pip-installs the
internal/qwen-web-arwaky package, installs Playwright Chromium, sets up
XDG data/state/cache dirs, and symlinks the launchers into ~/.local/bin/.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import (
    bin_home,
    tool_cache_dir,
    tool_config_dir,
    tool_data_dir,
    tool_state_dir,
)
from modules.tools.src.utility_tool_mechanics import ROOT, ensure_source, generic_owned
from modules.tools.src.utility_venv_helpers import (
    ensure_venv,
    install_package,
    setup_bin_links,
    setup_xdg_directories,
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


def _install_playwright(python_bin: Path) -> None:
    print("  [install] Installing Playwright Chromium...")
    subprocess.run([str(python_bin), "-m", "playwright", "install", "chromium"], check=True)


def _setup_qwen_web_dirs() -> None:
    data_dir = tool_data_dir(TOOL_NAME)
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
    print(f"  [ok] State: {state_dir}")
    print(f"  [ok] Cache: {cache_dir}")


class QwenWebAdapter:
    """Install/update internal/qwen-web-arwaky via a uv-managed venv + Playwright."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "qwen-web-arwaky").exists()

    # -- install (from old installer adapter, verbatim mechanics) ----------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        src_dir = root / SRC_REL

        print(">>> Installing qwen-web-arwaky (XDG compliant)...")
        if not ensure_source(root, SRC_REL):
            raise FileNotFoundError(f"source not found {src_dir}")

        python_bin = ensure_venv(TOOL_NAME, force=False)
        install_package(python_bin, src_dir, TOOL_NAME)
        _install_playwright(python_bin)
        _setup_qwen_web_dirs()
        setup_bin_links(python_bin, LAUNCHERS)

        print("\n>>> Successfully installed qwen-web-arwaky")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        print("    Run 'qwc init' to setup workspace symlinks")
        return [python_bin]

    # -- update (from old updater adapter) ---------------------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        source = root / SRC_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "venv/pip + Playwright (rebuild required)"

    def update(self, spec, root: Path) -> list[Path]:
        from modules.shared.src.utility_git_update import update_submodule, write_install_stamp

        print(">>> Updating qwen-web-arwaky (XDG compliant)...")

        if not update_submodule(root, SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {SRC_REL}")

        source = root / SRC_REL
        if not source.exists():
            raise ToolUpdateError(f"source not found {source}")

        python_bin = ensure_venv(TOOL_NAME, force=True)
        install_package(python_bin, source, TOOL_NAME)
        _install_playwright(python_bin)
        _setup_qwen_web_dirs()
        setup_bin_links(python_bin, LAUNCHERS)
        write_install_stamp(python_bin.parent.parent, TOOL_NAME, source)

        created = [bin_home() / name for name, _entry in LAUNCHERS]
        print("\n>>> Successfully updated qwen-web-arwaky")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        return created

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        return generic_owned(
            spec,
            [name for name, _e in LAUNCHERS],
            extra=[tool_config_dir(TOOL_NAME), tool_state_dir(TOOL_NAME), tool_cache_dir(TOOL_NAME)],
        )
