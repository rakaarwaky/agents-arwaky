#!/usr/bin/env python3
"""fetch-mcp installer (pengganti tools/fetch-mcp/install.sh)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import bin_home, data_home, ensure_bin_home  # noqa: E402

VENDOR_DIR = ROOT / "vendor/fetch-mcp"
TARGET_DIR = data_home() / "fetch-mcp"
LAUNCHER = bin_home() / "fetch-mcp"
ALIAS = bin_home() / "mcp-fetch"


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
    shutil.copytree(VENDOR_DIR / "dist", TARGET_DIR / "dist")
    shutil.copy2(VENDOR_DIR / "package.json", TARGET_DIR / "package.json")
    if (VENDOR_DIR / "node_modules").exists():
        shutil.copytree(VENDOR_DIR / "node_modules", TARGET_DIR / "node_modules", dirs_exist_ok=True)


def install_launcher():
    ensure_bin_home()
    content = '''#!/usr/bin/env python3
import os, sys
from pathlib import Path
data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "fetch-mcp"
cli = {"html","markdown","readable","txt","json","youtube","--help","-h","--version","-v"}
script = data / "dist" / ("cli.js" if (len(sys.argv) > 1 and sys.argv[1] in cli) else "index.js")
env = os.environ.copy()
env["NODE_PATH"] = str(data / "node_modules") + os.pathsep + env.get("NODE_PATH", "")
os.execvpe("node", ["node", str(script), *sys.argv[1:]], env)
'''
    LAUNCHER.write_text(content, encoding="utf-8")
    LAUNCHER.chmod(0o755)
    ALIAS.unlink(missing_ok=True)
    ALIAS.symlink_to(LAUNCHER)


def main() -> int:
    if not VENDOR_DIR.exists() or not (VENDOR_DIR / "package.json").exists():
        print(f"Error: Upstream source not found at {VENDOR_DIR}.", file=sys.stderr)
        print("Run 'git submodule update --init vendor/fetch-mcp' first.", file=sys.stderr)
        return 1
    print(f">>> Building Fetch-MCP into XDG Data Directory ({TARGET_DIR})...")
    build()
    print(f">>> Installing runtime to {TARGET_DIR}...")
    install_runtime()
    print(f">>> Installing launcher to {LAUNCHER}...")
    install_launcher()
    print(f">>> Successfully installed fetch-mcp -> {LAUNCHER} (and {ALIAS})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
