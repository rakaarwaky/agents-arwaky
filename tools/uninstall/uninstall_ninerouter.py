#!/usr/bin/env python3
"""9Router uninstaller (Python)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (  # type: ignore[import-untyped]
    agents_arwaky_config_dir,
    bin_home,
    cache_home,
    config_home,
    data_home,
    legacy_agents_arwaky_secret_dir,
)


def main() -> int:
    print(">>> Uninstalling 9Router...")
    daemon_py = ROOT / "tools/daemons/ninerouter_daemon.py"
    if daemon_py.exists():
        subprocess.run([sys.executable, str(daemon_py), "service-uninstall"], check=False)
    (bin_home() / "9router").unlink(missing_ok=True)
    (data_home() / "agents-arwaky/internal-bin/9router").unlink(missing_ok=True)
    shutil.rmtree(data_home() / "9router", ignore_errors=True)
    shutil.rmtree(config_home() / "9router", ignore_errors=True)
    shutil.rmtree(cache_home() / "9router", ignore_errors=True)
    shutil.rmtree(cache_home() / "agents-arwaky" / "build-9router", ignore_errors=True)
    # Hapus secret env kanonik + legacy (hanya file 9router, jangan hapus dir
    # agents-arwaky karena bisa berisi secret tool lain).
    for env in (
        agents_arwaky_config_dir() / "ninerouter.env",
        legacy_agents_arwaky_secret_dir() / "ninerouter.env",
    ):
        env.unlink(missing_ok=True)
    print(">>> 9router uninstalled (launchers + data + config + cache + secrets).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
