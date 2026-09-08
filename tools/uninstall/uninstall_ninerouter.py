#!/usr/bin/env python3
"""9Router uninstaller (Python) — delegates to shared remove_tool_artifacts()."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (
    agents_arwaky_config_dir,
    bin_home,
    data_home,
    legacy_agents_arwaky_secret_dir,
    remove_tool_artifacts,
)

LAUNCHERS = ["9router"]


def main() -> int:
    print(">>> Uninstalling 9Router...")

    # Stop daemon if registered
    daemon_py = ROOT / "tools/daemons/ninerouter_daemon.py"
    if daemon_py.exists():
        subprocess.run([sys.executable, str(daemon_py), "service-uninstall"], check=False)

    # Remove launcher + XDG artifacts via shared helper
    remove_tool_artifacts("9router", LAUNCHERS, clean_config=True)

    # Remove container-internal binary (per AGENTS.md invariant)
    internal_bin = data_home() / "agents-arwaky" / "internal-bin" / "9router"
    internal_bin.unlink(missing_ok=True)

    # Remove secret env files (tool-specific, not handled by remove_tool_artifacts)
    for env in (
        agents_arwaky_config_dir() / "ninerouter.env",
        legacy_agents_arwaky_secret_dir() / "ninerouter.env",
    ):
        env.unlink(missing_ok=True)

    print(">>> 9router uninstalled (launchers + data + config + cache + secrets).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
