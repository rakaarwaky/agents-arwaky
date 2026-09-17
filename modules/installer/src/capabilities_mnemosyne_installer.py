"""Mnemosyne installer (uv) — port of tools/install/install_mnemosyne.py.

vendor/mnemosyne is a Python package run via `uv run` (no venv copy).
The MCP stdio server lives in the [mcp] optional-dependency group, so the
launchers are written with `uv_args=["--extra", "mcp"]` — without it uv dies
with "MCP not installed" (mnemosyne.mcp_server ImportError).
"""
from __future__ import annotations

import subprocess

from modules.shared.src.launcher.capabilities_launcher_writer import write_uv_launchers
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.tool.contract_tool_protocol import IToolInstaller
from modules.shared.src.xdg.utility_xdg_atomic_io import ensure_bin_home
from modules.shared.src.xdg.utility_xdg_paths import bin_home


SRC_REL = "vendor/mnemosyne"
LAUNCHERS = [
    ("mnemosyne", "mnemosyne"),
    ("mnemosyne-mcp", "mnemosyne"),
]
# The MCP stdio server lives in the [mcp] optional-dependency group; uv run
# without it dies with "MCP not installed" (mnemosyne.mcp_server ImportError).
UV_ARGS = ["--extra", "mcp"]


class MnemosyneInstaller(IToolInstaller):
    """Install vendor/mnemosyne via uv-run launchers with the [mcp] extra."""

    def __init__(self, root=None) -> None:
        self._root = root or repo_root()

    def install(self, spec: ToolSpec) -> InstallResult:
        root = self._root
        if (bin_home() / "mnemosyne").exists():
            return InstallResult(True, spec.id, "mnemosyne is already installed")

        src_dir = root / SRC_REL
        if not src_dir.exists():
            subprocess.run(
                ["git", "-C", str(root), "submodule", "update", "--init", SRC_REL],
                check=False,
            )
        if not src_dir.exists():
            return InstallResult(False, spec.id, f"source not found {SRC_REL}")

        ensure_bin_home()
        created = write_uv_launchers(SRC_REL, LAUNCHERS, root=root, uv_args=UV_ARGS)
        for p in created:
            print(f"  -> {p}")
        return InstallResult(True, spec.id, "mnemosyne installed")
