#!/usr/bin/env python3
"""google-workspace-mcp uninstaller (Python)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, config_home, data_home


def main() -> int:
    print(">>> Uninstalling google-workspace-mcp...")
    for launcher in ['workspace-mcp', 'google-workspace-mcp']:
        (bin_home() / launcher).unlink(missing_ok=True)
    shutil.rmtree(data_home() / "google-workspace-mcp", ignore_errors=True)
    shutil.rmtree(config_home() / "google-workspace-mcp", ignore_errors=True)
    print(">>> google-workspace-mcp uninstalled (launchers + data + config).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
