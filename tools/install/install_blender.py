#!/usr/bin/env python3
"""Installer blender (Python, shared uv launcher writer)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from launcher_writer import write_uv_launchers  # type: ignore[import-not-found]

SRC_DIR = ROOT / "internal/blender-arwaky"


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_DIR}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", "internal/blender-arwaky"])
    write_uv_launchers("blender", "internal/blender-arwaky", ['blender-arwaky', 'ba', 'blender-mcp'], root=ROOT)
    print(">>> Successfully installed blender launchers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
