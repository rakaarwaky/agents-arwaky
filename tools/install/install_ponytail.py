#!/usr/bin/env python3
"""Installer ponytail — @dietrichgebert/ponytail (OpenCode plugin + MCP).

Specifics: ponytail has NO build script and no lockfile — so there is no
build step. Just copy source to $XDG_DATA_HOME/ponytail and install
ponytail-mcp dependencies (@modelcontextprotocol/sdk, zod) via npm.
Entry MCP = ponytail-mcp/index.js.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import (  # type: ignore[import-not-found]
    atomic_write_text,
    bin_home,
    data_home,
    ensure_bin_home,
    warn_if_bin_not_on_path,
)

SRC = ROOT / "vendor/ponytail"
APP_DIR = data_home() / "ponytail"
ENTRY = "ponytail-mcp/index.js"

# Old node_modules in vendor are not copied (may be stale); deps are reinstalled
# with npm --prefix inside APP_DIR/ponytail-mcp.
IGNORES = shutil.ignore_patterns(
    "node_modules", ".git", "__pycache__", "*.egg-info", ".venv", "venv",
)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


def _require(tool: str, reason: str) -> bool:
    if shutil.which(tool):
        return True
    print(f"Error: {tool} not found in PATH. {reason}", file=sys.stderr)
    return False


def main() -> int:
    if not (SRC / "package.json").exists():
        print("Error: ponytail source not found (submodule not initialized).", file=sys.stderr)
        return 1
    if not _require("npm", "ponytail requires npm (https://nodejs.org)"):
        return 1

    print(f">>> Installing ponytail (no build) into {APP_DIR}...")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    shutil.copytree(SRC, APP_DIR, ignore=IGNORES)

    mcp_dir = APP_DIR / "ponytail-mcp"
    if (mcp_dir / "package.json").exists():
        run(["npm", "install", "--no-audit", "--no-fund"], mcp_dir)

    entry = APP_DIR / ENTRY
    if not entry.exists():
        print(f"  Error: entry not found {entry}", file=sys.stderr)
        return 1

    ensure_bin_home()
    launcher = bin_home() / "ponytail-mcp"
    launcher.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f'entry = r"{entry}"\n'
        'os.execvpe("node", ["node", entry, *sys.argv[1:]], os.environ.copy())\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    print(f"  -> {launcher}")

    warn_if_bin_not_on_path()
    print(">>> Successfully installed ponytail")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
