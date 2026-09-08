#!/usr/bin/env python3
"""anytype-daemon uninstaller (Python) — container service + launchers."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (
    bin_home,
    config_home,
    data_home,
    remove_tool_artifacts,
)


def main() -> int:
    print(">>> Uninstalling anytype-daemon...")

    # Disable systemd user service if present
    unit = config_home() / "systemd/user/anytype-daemon.service"
    if unit.exists() and shutil.which("systemctl"):
        subprocess.run(["systemctl", "--user", "disable", "--now", "anytype-daemon.service"],
                       check=False, capture_output=True)
        unit.unlink(missing_ok=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False, capture_output=True)
        print("  -> systemd service anytype-daemon removed")

    # Launcher + alias ad + internal-bin copy
    remove_tool_artifacts("anytype-daemon", ["anytype-daemon", "ad"], clean_config=False)
    (data_home() / "agents-arwaky/internal-bin/anytype-daemon").unlink(missing_ok=True)

    if "--purge" in sys.argv:
        shutil.rmtree(data_home() / "anytype", ignore_errors=True)
        shutil.rmtree(data_home() / "anytype-mcp", ignore_errors=True)
        print("  -> anytype data purged")

    print(">>> anytype-daemon uninstalled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
