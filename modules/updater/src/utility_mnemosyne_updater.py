"""Mnemosyne updater adapter — leaf utility for one manifest tool.

Mirrors the original tools/update/update_mnemosyne.py mechanics: submodule
bump, uv launchers rewritten with the same baked-root content the
installer produces (kept local so adapters stay free of cross-feature
imports).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    ensure_path,
    warn_if_bin_not_on_path,
)
from modules.shared.src.taxonomy_xdg_paths import bin_home
from modules.shared.src.utility_git_update import update_submodule
from modules.shared.src.taxonomy_tool_vo import ToolSpec

SRC_REL = "vendor/mnemosyne"
LAUNCHERS = [
    ("mnemosyne", "mnemosyne"),
    ("mnemosyne-mcp", "mnemosyne"),
]
# MCP stdio server needs the [mcp] optional-dependency group in the uv runtime.
UV_ARGS = ["--extra", "mcp"]


def _write_uv_launcher(name: str, entry: str, root: Path) -> Path:
    """Same `uv run --extra mcp` launcher content the installer writes."""
    ensure_bin_home()
    baked_root = str(root)
    extra = "".join(repr(a) + ", " for a in UV_ARGS)
    target = bin_home() / name
    content = (
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        f'root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {repr(baked_root)}))\n'
        f'os.execvpe("uv", ["uv", "run", {extra}"--directory", str(root / "{SRC_REL}"), '
        f'"{entry}", *sys.argv[1:]], os.environ.copy())\n'
    )
    atomic_write_text(target, content)
    warn_if_bin_not_on_path()
    ensure_path()
    return target


class MnemosyneUpdaterAdapter:
    """Mnemosyne (uv, [mcp] extra) update sequence."""

    def is_pin_satisfied(self, spec: ToolSpec, root: Path) -> tuple[bool, str]:
        source = root / SRC_REL
        if not source.exists():
            return False, "submodule not initialized"
        return False, "uv project (rebuild required)"

    def update(self, spec: ToolSpec, root: Path) -> list[Path]:
        source = root / SRC_REL
        if not update_submodule(root, SRC_REL):
            raise ToolUpdateError(f"submodule update failed: {SRC_REL}")
        if not source.exists():
            raise ToolUpdateError(f"source not found {source}")

        created = [_write_uv_launcher(name, entry, root) for name, entry in LAUNCHERS]
        for path in created:
            print(f"  -> {path}")
        print(">>> Successfully updated mnemosyne")
        return created
