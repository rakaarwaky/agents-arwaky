#!/usr/bin/env python3
"""codegraph uninstaller (Python)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, config_home, data_home  # type: ignore[import-untyped]


def main() -> int:
    print(">>> Uninstalling codegraph...")
    for launcher in ['codegraph-mcp']:
        (bin_home() / launcher).unlink(missing_ok=True)
    for alias in ['codegraph']:
        (bin_home() / alias).unlink(missing_ok=True)
    shutil.rmtree(data_home() / "codegraph", ignore_errors=True)
    shutil.rmtree(config_home() / "codegraph", ignore_errors=True)
    print(">>> codegraph uninstalled (launchers + data + config).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
