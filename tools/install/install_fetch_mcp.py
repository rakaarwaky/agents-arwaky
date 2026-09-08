#!/usr/bin/env python3
"""Installer fetch-mcp (Python, shared node installer + dual launcher)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from utility_node_installer import build, install_runtime
from xdg import bin_home, data_home

VENDOR_DIR = ROOT / "vendor/fetch-mcp"
TARGET_DIR = data_home() / "fetch-mcp"


def main() -> int:
    if not VENDOR_DIR.exists() or not (VENDOR_DIR / "package.json").exists():
        print(f"Error: Upstream source not found at {VENDOR_DIR}.", file=sys.stderr)
        return 1
    print(f">>> Building fetch-mcp into {TARGET_DIR}...")
    build(VENDOR_DIR)
    install_runtime(VENDOR_DIR, TARGET_DIR)
    # Dual MCP/CLI launcher khusus fetch
    content = """#!/usr/bin/env python3
import os, sys
from pathlib import Path
data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "fetch-mcp"
cli = {"html","markdown","readable","txt","json","youtube","--help","-h","--version","-v"}
script = data / "dist" / ("cli.js" if (len(sys.argv) > 1 and sys.argv[1] in cli) else "index.js")
env = os.environ.copy()
env["NODE_PATH"] = str(data / "node_modules") + os.pathsep + env.get("NODE_PATH", "")
os.execvpe("node", ["node", str(script), *sys.argv[1:]], env)
"""
    launcher = bin_home() / "fetch-mcp"
    launcher.write_text(content, encoding="utf-8")
    launcher.chmod(0o755)
    (bin_home() / "mcp-fetch").unlink(missing_ok=True)
    (bin_home() / "mcp-fetch").symlink_to(launcher)
    print(f">>> Successfully installed fetch-mcp -> {launcher} (and mcp-fetch)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
