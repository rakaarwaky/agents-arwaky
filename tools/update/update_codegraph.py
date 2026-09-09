#!/usr/bin/env python3
"""Updater codegraph — force reinstall @colbymchenry/codegraph (TypeScript, npm).

Always removes APP_DIR and rebuilds from source.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (
    atomic_write_text,
    bin_home,
    data_home,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)

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
    sys.path.insert(0, str(ROOT / "tools" / "lib"))
    from git_update import update_submodule
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


if __name__ == "__main__":
    raise SystemExit(main())
