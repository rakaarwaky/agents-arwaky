#!/usr/bin/env python3
"""context7 installer (Python)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, data_home, ensure_bin_home  # noqa: E402

VENDOR_DIR = ROOT / "vendor/context7"
TARGET_DIR = data_home() / "context7"
LAUNCHER = bin_home() / "context7-mcp"


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def build():
    if shutil.which("bun"):
        run(["bun", "install"], VENDOR_DIR)
        run(["bun", "run", "build"], VENDOR_DIR)
    elif shutil.which("npm"):
        run(["npm", "install", "--no-audit", "--no-fund"], VENDOR_DIR)
        run(["npm", "run", "build"], VENDOR_DIR)
    else:
        raise RuntimeError("Neither bun nor npm found.")


def install_runtime():
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    if (VENDOR_DIR / "dist").exists():
        shutil.copytree(VENDOR_DIR / "dist", TARGET_DIR / "dist")
    shutil.copy2(VENDOR_DIR / "package.json", TARGET_DIR / "package.json")
    if (VENDOR_DIR / "node_modules").exists():
        shutil.copytree(VENDOR_DIR / "node_modules", TARGET_DIR / "node_modules", dirs_exist_ok=True)


def install_launcher():
    ensure_bin_home()
    content = """#!/usr/bin/env python3
import os, sys
from pathlib import Path
data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "context7"
os.execvpe("node", ["node", str(data / "dist" / "index.js"), *sys.argv[1:]], os.environ.copy())
"""
    LAUNCHER.write_text(content, encoding="utf-8")
    LAUNCHER.chmod(0o755)
    for alias in ['ctx7']:
        a = bin_home() / alias
        a.unlink(missing_ok=True)
        a.symlink_to(LAUNCHER)


def main() -> int:
    if not VENDOR_DIR.exists() or not (VENDOR_DIR / "package.json").exists():
        print(f"Error: Upstream source not found at {VENDOR_DIR}.", file=sys.stderr)
        return 1
    print(f">>> Building context7 into {TARGET_DIR}...")
    build()
    install_runtime()
    install_launcher()
    print(f">>> Successfully installed context7 -> {LAUNCHER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
