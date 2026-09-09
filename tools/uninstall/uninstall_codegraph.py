#!/usr/bin/env python3
"""codegraph uninstaller (Python)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from paths import repo_root
ROOT = repo_root()
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import remove_tool_artifacts


def main() -> int:
    print(">>> Uninstalling codegraph...")
    remove_tool_artifacts("codegraph", ['codegraph-mcp', 'codegraph'])
    print(">>> codegraph uninstalled (launchers + data + config + cache).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
