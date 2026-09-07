#!/usr/bin/env python3
"""9Router installer (Python) — hybrid daemon + launcher."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, data_home, ensure_bin_home  # noqa: E402

TOOL_DIR = ROOT / "tools/9router"
DATA_DIR = data_home() / "9router"
INTERNAL_BIN = data_home() / "agents-arwaky/internal-bin"
LAUNCHER = bin_home() / "9router"


def main() -> int:
    ensure_bin_home()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    daemon_py = TOOL_DIR / "daemon/9router_daemon.py"
    print(">>> Setting up 9Router hybrid architecture...")
    if daemon_py.exists():
        subprocess.run([sys.executable, str(daemon_py), "service-install"], check=False)
    launcher_content = '''#!/usr/bin/env python3
import os, sys
from pathlib import Path
root = Path(os.environ.get("AGENTS_ARWAKY_ROOT", str(Path.home() / "agents-arwaky")))
daemon = root / "tools/9router/daemon/9router_daemon.py"
os.execvpe("python3", ["python3", str(daemon), *sys.argv[1:]], os.environ.copy())
'''
    LAUNCHER.write_text(launcher_content, encoding="utf-8")
    LAUNCHER.chmod(0o755)
    INTERNAL_BIN.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LAUNCHER, INTERNAL_BIN / "9router")
    (INTERNAL_BIN / "9router").chmod(0o755)
    print(f">>> Successfully installed 9Router -> {LAUNCHER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
