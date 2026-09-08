#!/usr/bin/env python3
"""lint-arwaky uninstaller (Python)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import remove_tool_artifacts  # type: ignore[import-untyped]


def main() -> int:
    print(">>> Uninstalling lint-arwaky...")
    remove_tool_artifacts("lint-arwaky", ['lint-arwaky', 'la', 'lint-arwaky-cli', 'lint-arwaky-mcp', 'lint-arwaky-tui', 'lac'])
    print(">>> lint-arwaky uninstalled (launchers + data + config + cache).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
