#!/usr/bin/env python3
"""anytype-mcp uninstaller (Python)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, data_home, config_home  # noqa: E402


def main() -> int:
    print(">>> Uninstalling anytype-mcp...")
    for launcher in ['anytype-mcp']:
        (bin_home() / launcher).unlink(missing_ok=True)
    for alias in []:
        (bin_home() / alias).unlink(missing_ok=True)
    shutil.rmtree(data_home() / "anytype-mcp", ignore_errors=True)
    shutil.rmtree(config_home() / "anytype-mcp", ignore_errors=True)
    print(">>> anytype-mcp uninstalled (launchers + data + config).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
