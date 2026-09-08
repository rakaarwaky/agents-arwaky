#!/usr/bin/env python3
"""mnemosyne uninstaller (Python)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import remove_tool_artifacts


def main() -> int:
    print(">>> Uninstalling mnemosyne...")
    remove_tool_artifacts("mnemosyne", ['mnemosyne', 'mnemosyne-mcp'])
    print(">>> mnemosyne uninstalled (launchers + data + config + cache).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
