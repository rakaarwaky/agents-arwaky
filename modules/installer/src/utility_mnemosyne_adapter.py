"""Mnemosyne adapter (uv) — port of tools/install/install_mnemosyne.py.

vendor/mnemosyne is a Python package run via `uv run` (no venv copy).
The MCP stdio server lives in the [mcp] optional-dependency group, so the
launchers are written with `uv_args=["--extra", "mcp"]` — without it uv dies
with "MCP not installed" (mnemosyne.mcp_server ImportError).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.shared.src.taxonomy_tool_vo import ToolSpec
from modules.installer.src.utility_adapter_base import AdapterBase, ROOT
from modules.installer.src.utility_launcher_writer import write_uv_launchers

SRC_REL = "vendor/mnemosyne"
LAUNCHERS = [
    ("mnemosyne", "mnemosyne"),
    ("mnemosyne-mcp", "mnemosyne"),
]
# The MCP stdio server lives in the [mcp] optional-dependency group; uv run
# without it dies with "MCP not installed" (mnemosyne.mcp_server ImportError).
UV_ARGS = ["--extra", "mcp"]


class MnemosyneAdapter(AdapterBase):
    """Install vendor/mnemosyne via uv-run launchers with the [mcp] extra."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "mnemosyne").exists()

    def install(self, spec: ToolSpec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        src_dir = root / SRC_REL
        if not self.ensure_source(root, SRC_REL):
            raise FileNotFoundError(f"source not found {src_dir}")

        created = write_uv_launchers(SRC_REL, LAUNCHERS, root=root, uv_args=UV_ARGS)
        for p in created:
            print(f"  -> {p}")
        print(">>> Successfully installed mnemosyne")
        return created
