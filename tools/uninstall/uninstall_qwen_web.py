#!/usr/bin/env python3
"""qwen-web uninstaller (Python)."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, config_home, data_home


def main() -> int:
    print(">>> Uninstalling qwen-web...")
    for launcher in ['qwen-web-arwaky', 'qwa', 'qwen-web-cli', 'qwen-web-mcp', 'qwc']:
        (bin_home() / launcher).unlink(missing_ok=True)
    shutil.rmtree(data_home() / "qwen-web", ignore_errors=True)
    shutil.rmtree(config_home() / "qwen-web", ignore_errors=True)
    print(">>> qwen-web uninstalled (launchers + data + config).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
