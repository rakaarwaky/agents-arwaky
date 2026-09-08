#!/usr/bin/env python3
"""context7 uninstaller (Python)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, config_home, data_home


def main() -> int:
    print(">>> Uninstalling context7...")
    for launcher in ['context7-mcp']:
        (bin_home() / launcher).unlink(missing_ok=True)
    for alias in ['ctx7']:
        (bin_home() / alias).unlink(missing_ok=True)
    shutil.rmtree(data_home() / "context7", ignore_errors=True)
    shutil.rmtree(config_home() / "context7", ignore_errors=True)
    print(">>> context7 uninstalled (launchers + data + config).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
