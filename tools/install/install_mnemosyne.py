#!/usr/bin/env python3
"""Installer mnemosyne — mnemosyne (Python, uv). MCP entry maps to main CLI."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from paths import repo_root
ROOT = repo_root()
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from launcher_writer import write_uv_launchers
from xdg import bin_home, ensure_bin_home

SRC_REL = "vendor/mnemosyne"
SRC_DIR = ROOT / SRC_REL
LAUNCHERS = [
    ("mnemosyne", "mnemosyne"),
    ("mnemosyne-mcp", "mnemosyne"),
]
# The MCP stdio server lives in the [mcp] optional-dependency group; uv run
# without it dies with "MCP not installed" (mnemosyne.mcp_server ImportError).
UV_ARGS = ["--extra", "mcp"]
def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)
def is_installed() -> bool:
    """Check if mnemosyne is already installed (binary exists)."""
    return (bin_home() / "mnemosyne").exists()


def main() -> int:
    if is_installed():
        print(">>> mnemosyne is already installed. Use 'aa update mnemosyne' to reinstall.")
        return 0

    if not SRC_DIR.exists():
        print(f">>> Initializing submodule {SRC_REL}...", file=sys.stderr)
        run(["git", "-C", str(ROOT), "submodule", "update", "--init", SRC_REL])
    if not SRC_DIR.exists():
        print(f"Error: source not found {SRC_DIR}.", file=sys.stderr)
        return 1

    ensure_bin_home()
    created = write_uv_launchers(SRC_REL, LAUNCHERS, root=ROOT, uv_args=UV_ARGS)
    for p in created:
        print(f"  -> {p}")
    print(">>> Successfully installed mnemosyne")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
