#!/usr/bin/env python3
"""Updater workspace — force reinstall google-workspace-mcp (Python, uv).

Always recreates launchers.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from launcher_writer import write_uv_launchers
from xdg import ensure_bin_home

SRC_REL = "vendor/google-workspace-mcp"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [
    ("workspace-mcp", "workspace-mcp"),
    ("google-workspace-mcp", "workspace-mcp"),
]


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
    created = write_uv_launchers(SRC_REL, LAUNCHERS, root=ROOT)
    for p in created:
        print(f"  -> {p}")
    print(">>> Successfully updated google-workspace-mcp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
