#!/usr/bin/env python3
"""9Router uninstaller (Python)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, data_home  # noqa: E402


def main() -> int:
    print(">>> Uninstalling 9Router...")
    daemon_py = ROOT / "tools/9router/daemon/9router_daemon.py"
    if daemon_py.exists():
        subprocess.run([sys.executable, str(daemon_py), "service-uninstall"], check=False)
    (bin_home() / "9router").unlink(missing_ok=True)
    (data_home() / "agents-arwaky/internal-bin/9router").unlink(missing_ok=True)
    shutil.rmtree(data_home() / "9router", ignore_errors=True)
    print(">>> 9router uninstalled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
