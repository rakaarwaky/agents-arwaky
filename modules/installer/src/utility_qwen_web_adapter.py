"""Qwen-web-arwaky adapter (uv venv + Playwright) — verbatim port of tools/install/install_qwen_web.py.

Creates a venv in ~/.local/share/qwen-web/venv/, pip-installs the
internal/qwen-web-arwaky package, installs Playwright Chromium, and symlinks
the launchers into ~/.local/bin/.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from modules.installer.src.utility_adapter_base import AdapterBase, ROOT
from modules.installer.src.utility_venv_helpers import ensure_venv, install_package, setup_bin_links

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
    from modules.shared.src.taxonomy_xdg_paths import tool_cache_dir, tool_data_dir, tool_state_dir

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


class QwenWebAdapter(AdapterBase):
    """Install internal/qwen-web-arwaky via a uv-managed venv + Playwright."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        from modules.shared.src.taxonomy_xdg_paths import bin_home
        return (bin_home() / "qwen-web-arwaky").exists()

    def install(self, spec: ToolSpec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        from modules.shared.src.taxonomy_xdg_paths import tool_data_dir

        root = root or ROOT
        src_dir = root / SRC_REL

        print(">>> Installing qwen-web-arwaky (XDG compliant)...")
        if not self.ensure_source(root, SRC_REL):
            raise FileNotFoundError(f"source not found {src_dir}")

        python_bin = ensure_venv(TOOL_NAME, force=False)
        install_package(python_bin, src_dir, TOOL_NAME)
        _install_playwright(python_bin)
        _setup_qwen_web_dirs()
        setup_bin_links(python_bin, LAUNCHERS)

        print("\n>>> Successfully installed qwen-web-arwaky")
        print(f"    Venv: {python_bin.parent}")
        print(f"    Data: {tool_data_dir(TOOL_NAME)}")
        print(f"    Run 'qwc init' to setup workspace symlinks")
        return [python_bin]
