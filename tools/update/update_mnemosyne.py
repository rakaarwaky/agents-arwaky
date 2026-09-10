#!/usr/bin/env python3
"""Updater mnemosyne — force reinstall mnemosyne (Python, uv).

Always recreates launchers.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from paths import repo_root
ROOT = repo_root()
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from launcher_writer import write_uv_launchers
from xdg import ensure_bin_home

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
    sys.path.insert(0, str(ROOT / "tools" / "lib"))
    from git_update import update_submodule
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


if __name__ == "__main__":
    raise SystemExit(main())
