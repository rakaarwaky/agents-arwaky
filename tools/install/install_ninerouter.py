#!/usr/bin/env python3
"""9Router installer (Python) — hybrid daemon + launcher."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (  # type: ignore[import-untyped]
    atomic_write_text,
    bin_home,
    data_home,
    ensure_bin_home,
    ensure_path,
)

TOOL_DIR = ROOT / "tools/daemons"
DATA_DIR = data_home() / "9router"
INTERNAL_BIN = data_home() / "agents-arwaky/internal-bin"
LAUNCHER = bin_home() / "9router"


def main() -> int:
    ensure_bin_home()
    ensure_path()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    daemon_py = TOOL_DIR / "ninerouter_daemon.py"
    print(">>> Setting up 9Router hybrid architecture...")
    if daemon_py.exists():
        subprocess.run(
            [sys.executable, str(daemon_py), "service-install"], check=False
        )
    launcher_content = f'''#!/usr/bin/env python3
import os, sys
from pathlib import Path
root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", {str(ROOT)!r}))
daemon = root / "tools/daemons/ninerouter_daemon.py"
os.execvpe("python3", ["python3", str(daemon), *sys.argv[1:]], os.environ.copy())
'''
    atomic_write_text(LAUNCHER, launcher_content)
    INTERNAL_BIN.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LAUNCHER, INTERNAL_BIN / "9router")
    (INTERNAL_BIN / "9router").chmod(0o755)
    print(f">>> Successfully installed 9Router -> {LAUNCHER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
