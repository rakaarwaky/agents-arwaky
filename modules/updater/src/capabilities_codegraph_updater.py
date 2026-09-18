"""Codegraph updater — VERBATIM port of tools/update/update_codegraph.py.

Keep the ENTIRE original body: every function, every constant, every
print statement, every edge-case message, every subprocess call, exactly
as written in the original. The ONLY differences:
1. Import paths (all AES equivalents under modules/shared/src/).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from modules.shared.src.utility_paths import repo_root

ROOT = repo_root()

from modules.shared.src.utility_xdg_atomic_io import (
    atomic_write_text,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)
from modules.shared.src.utility_xdg_paths import bin_home, data_home
from modules.shared.src.utility_git_update import update_submodule
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.updater.src.contract_tool_updater import IToolUpdater

SRC = ROOT / "vendor/codegraph"
APP_DIR = data_home() / "codegraph"
ENTRY = "dist/bin/codegraph.js"
LAUNCHERS = ["codegraph-mcp", "codegraph"]

IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "target", "*.egg-info",
    ".venv", "venv", "*.tsbuildinfo",
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def _require(tool: str, reason: str) -> bool:
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False


def main() -> int:
    # Pull latest from remote
    update_submodule(ROOT, "vendor/codegraph")

    if not (SRC / "package.json").exists():
        print("Error: codegraph source not found (submodule not initialized).", file=sys.stderr)
        return 1
    if not _require("npm", "codegraph requires npm (https://nodejs.org)"):
        return 1

    print(f">>> Updating codegraph into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    run(["npm", "ci", "--no-audit", "--no-fund"], APP_DIR)
    run(["npm", "run", "build"], APP_DIR)

    entry = APP_DIR / ENTRY
    if not entry.exists():
        print(f"  Error: entry not found {entry}", file=sys.stderr)
        return 1

    ensure_bin_home()
    for name in LAUNCHERS:
        launcher = bin_home() / name
        atomic_write_text(launcher,
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            f'entry = r"{entry}"\n'
            'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n')
        print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully updated codegraph")
    return 0


class CodegraphUpdater(IToolUpdater):
    def __init__(self, root=None) -> None:
        self._root = root or ROOT

    def update(self, spec: ToolSpec) -> UpdateResult:
        rc = main()
        return UpdateResult(rc == 0, spec.id, "codegraph updated" if rc == 0 else "codegraph update failed")
