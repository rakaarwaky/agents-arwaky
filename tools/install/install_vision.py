#!/usr/bin/env python3
"""Installer vision (Python, shared uv launcher writer)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from utility_launcher_writer import write_uv_launchers

SRC_DIR = ROOT / "internal/vision-arwaky"


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_DIR}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", "internal/vision-arwaky"])
    write_uv_launchers("vision", "internal/vision-arwaky", ['vision-arwaky', 'vision-arwaky-cli', 'va', 'vision-arwaky-mcp'])
    print(">>> Successfully installed vision launchers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
