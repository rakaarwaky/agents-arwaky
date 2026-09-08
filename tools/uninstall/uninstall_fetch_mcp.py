#!/usr/bin/env python3
"""fetch-mcp uninstaller (pengganti tools/fetch-mcp/uninstall.sh)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, data_home  # type: ignore[import-untyped]


def main() -> int:
    print(">>> Uninstalling fetch-mcp...")
    for name in ("fetch-mcp", "mcp-fetch"):
        (bin_home() / name).unlink(missing_ok=True)
    shutil.rmtree(data_home() / "fetch-mcp", ignore_errors=True)
    print(">>> fetch-mcp uninstalled (launchers + data).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
