"""Mnemosyne adapter (uv, [mcp] extra) — unified install + update + teardown.

vendor/mnemosyne is a Python package run via `uv run` (no venv copy).
The MCP stdio server lives in the [mcp] optional-dependency group, so the
launchers are written with `uv_args=["--extra", "mcp"]` — without it uv dies
with "MCP not installed" (mnemosyne.mcp_server ImportError).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.tools.src.utility_adapter_base import AdapterBase, ROOT
from modules.tools.src.utility_launcher_writer import write_uv_launchers

SRC_REL = "vendor/mnemosyne"
LAUNCHERS = [
    ("mnemosyne", "mnemosyne"),
    ("mnemosyne-mcp", "mnemosyne"),
]
# The MCP stdio server lives in the [mcp] optional-dependency group; uv run
# without it dies with "MCP not installed" (mnemosyne.mcp_server ImportError).
UV_ARGS = ["--extra", "mcp"]


class MnemosyneAdapter(AdapterBase):
    """Install/update vendor/mnemosyne via uv-run launchers with the [mcp] extra."""

    def satisfied(self, spec, root: Path | None = None) -> bool:
        return (bin_home() / "mnemosyne").exists()

    def _write_launchers(self, root: Path) -> list[Path]:
        created = write_uv_launchers(SRC_REL, LAUNCHERS, root=root, uv_args=UV_ARGS)
        for p in created:
            print(f"  -> {p}")
        return created

    # -- install (from old installer adapter, verbatim mechanics) ----------------
    def install(self, spec, root: Path = ROOT, *, daemons=None) -> list[Path]:
        root = root or ROOT
        src_dir = root / SRC_REL
        if not self.ensure_source(root, SRC_REL):
            raise FileNotFoundError(f"source not found {src_dir}")

        created = self._write_launchers(root)
        print(">>> Successfully installed mnemosyne")
        return created

    # -- update (from old updater adapter) ---------------------------------------
    def is_pin_satisfied(self, spec, root: Path) -> tuple[bool, str]:
        source = root / SRC_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "uv project (rebuild required)"

    def update(self, spec, root: Path) -> list[Path]:
        from modules.shared.src.utility_git_update import update_submodule

        source = root / SRC_REL
        if not update_submodule(root, SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
        if not source.exists():
            raise ToolUpdateError(f"source not found {source}")

        created = self._write_launchers(root)
        print(">>> Successfully updated mnemosyne")
        return created

    # -- teardown data --------------------------------------------------------------
    def owned_paths(self, spec, root: Path | None = None) -> list[Path]:
        return self.generic_owned(spec, ["mnemosyne", "mnemosyne-mcp"])
