"""Mnemosyne updater — VERBATIM port of tools/update/update_mnemosyne.py.

Keep the ENTIRE original body: every function, every constant, every
print statement, every edge-case message, every subprocess call, exactly
as written in the original. The ONLY differences:
1. Import paths (all AES equivalents under modules/shared/src/).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.utility_paths import repo_root

ROOT = repo_root()

from modules.installer.src.utility_launcher_writer import write_uv_launchers
from modules.shared.src.utility_xdg_atomic_io import ensure_bin_home
from modules.shared.src.utility_git_update import update_submodule
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.updater.src.contract_tool_updater import IToolUpdater

SRC_REL = "vendor/mnemosyne"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [
    ("mnemosyne", "mnemosyne"),
    ("mnemosyne-mcp", "mnemosyne"),
]
# Keep in sync with tools/install/install_mnemosyne.py: MCP stdio server needs
# the [mcp] optional-dependency group in the uv runtime.
UV_ARGS = ["--extra", "mcp"]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    # Pull latest from remote
    update_submodule(ROOT, SRC_REL)

    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    ensure_bin_home()
    created = write_uv_launchers(SRC_REL, LAUNCHERS, root=ROOT, uv_args=UV_ARGS)
    for p in created:
        print(f"  -> {p}")
    print(">>> Successfully updated mnemosyne")
    return 0


class MnemosyneUpdater(IToolUpdater):
    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def update(self, spec: ToolSpec) -> UpdateResult:
        rc = main()
        return UpdateResult(rc == 0, spec.id, "mnemosyne updated" if rc == 0 else "mnemosyne update failed")
