#!/usr/bin/env python3
"""Installer mnemosyne (Python, shared uv launcher writer)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from utility_launcher_writer import write_uv_launchers  # type: ignore[import-not-found]

SRC_DIR = ROOT / "vendor/mnemosyne"


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_DIR}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", "vendor/mnemosyne"])
    write_uv_launchers("mnemosyne", "vendor/mnemosyne", ['mnemosyne', 'mnemosyne-mcp'])
    print(">>> Successfully installed mnemosyne launchers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
