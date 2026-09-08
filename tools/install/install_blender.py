#!/usr/bin/env python3
"""Installer blender — blender-arwaky (Python, uv): full name + alias ba."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from launcher_writer import write_uv_launchers  # type: ignore[import-not-found]
from xdg import ensure_bin_home  # type: ignore[import-not-found]

SRC_REL = "internal/blender-arwaky"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [
    ("blender-arwaky", "blender-arwaky"),
    ("ba", "blender-arwaky"),
    ("blender-mcp", "blender-mcp"),
]


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_REL}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", SRC_REL])
    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    ensure_bin_home()
    created = write_uv_launchers(SRC_REL, LAUNCHERS, root=ROOT)
    for p in created:
        print(f"  -> {p}")
    print(">>> Successfully installed blender-arwaky")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
