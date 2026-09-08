#!/usr/bin/env python3
"""lint-arwaky uninstaller (Python)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, config_home, data_home


def main() -> int:
    print(">>> Uninstalling lint-arwaky...")
    for b in ("lint-arwaky", "la", "lint-arwaky-cli", "lint-arwaky-mcp", "lint-arwaky-tui", "lac"):
        (bin_home() / b).unlink(missing_ok=True)
    shutil.rmtree(data_home() / "lint-arwaky", ignore_errors=True)
    shutil.rmtree(config_home() / "lint-arwaky", ignore_errors=True)
    print(">>> lint-arwaky uninstalled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
