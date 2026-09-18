"""Mnemosyne installer (uv) — verbatim port of tools/install/install_mnemosyne.py.

vendor/mnemosyne is a Python package run via `uv run` (no venv copy).
The MCP stdio server lives in the [mcp] optional-dependency group, so the
launchers are written with `uv_args=["--extra", "mcp"]` — without it uv dies
with "MCP not installed" (mnemosyne.mcp_server ImportError).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.installer.src.contract_tool_installer import IToolInstaller
from modules.installer.src.utility_launcher_writer import write_uv_launchers
from modules.shared.src.utility_xdg_atomic_io import ensure_bin_home
from modules.shared.src.utility_xdg_paths import bin_home

ROOT = repo_root()

SRC_REL = "vendor/mnemosyne"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [
    ("mnemosyne", "mnemosyne"),
    ("mnemosyne-mcp", "mnemosyne"),
]
# The MCP stdio server lives in the [mcp] optional-dependency group; uv run
# without it dies with "MCP not installed" (mnemosyne.mcp_server ImportError).
UV_ARGS = ["--extra", "mcp"]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def is_installed() -> bool:
    """Check if mnemosyne is already installed (binary exists)."""
    return (bin_home() / "mnemosyne").exists()


def _install_mnemosyne() -> int:
    if is_installed():
        print(">>> mnemosyne is already installed. Use 'aa update mnemosyne' to reinstall.")
        return 0

    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_REL}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", SRC_REL])
    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    ensure_bin_home()
    created = write_uv_launchers(SRC_REL, LAUNCHERS, root=ROOT, uv_args=UV_ARGS)
    for p in created:
        print(f"  -> {p}")
    print(">>> Successfully installed mnemosyne")
    return 0


class MnemosyneInstaller(IToolInstaller):
    """Install vendor/mnemosyne via uv-run launchers with the [mcp] extra."""

    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def install(self, spec: ToolSpec) -> InstallResult:
        rc = _install_mnemosyne()
        return InstallResult(
            rc == 0,
            spec.id,
            "mnemosyne installed" if rc == 0 else "mnemosyne install failed",
        )
