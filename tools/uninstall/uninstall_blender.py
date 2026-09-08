#!/usr/bin/env python3
"""blender uninstaller (Python)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import remove_tool_artifacts  # type: ignore[import-untyped]


def main() -> int:
    print(">>> Uninstalling blender...")
    remove_tool_artifacts("blender", ['blender-arwaky', 'ba', 'blender-mcp'])
    print(">>> blender uninstalled (launchers + data + config + cache).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
