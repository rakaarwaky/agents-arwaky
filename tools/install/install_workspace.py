#!/usr/bin/env python3
"""Installer workspace (Python, shared uv launcher writer)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from utility_launcher_writer import write_uv_launchers  # type: ignore[import-not-found]

SRC_DIR = ROOT / "vendor/google-workspace-mcp"


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_DIR}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", "vendor/google-workspace-mcp"])
    write_uv_launchers("workspace", "vendor/google-workspace-mcp", ['workspace-mcp', 'google-workspace-mcp'])
    print(">>> Successfully installed workspace launchers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
