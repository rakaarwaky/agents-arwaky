#!/usr/bin/env python3
"""One-shot ecosystem update (Python) — pengganti sync-all.sh."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from ui import info, ok, warn  # noqa: E402


def run(cmd):
    return subprocess.run(cmd).returncode


def main(argv):
    no_connect = "--no-connect" in argv
    no_build = "--no-build" in argv
    info("Running one-shot ecosystem sync...")

    info("Step 1: syncing submodules...")
    run(["git", "-C", str(ROOT), "submodule", "update", "--init", "--recursive", "vendor/", "internal/"])

    if not no_build:
        info("Step 2: building tools...")
        run([sys.executable, str(ROOT / "tools/arwaky/arwaky.py"), "install"])

    info("Step 3: generating MCP config...")
    run([sys.executable, str(ROOT / "tools/mcp/generate_config.py")])

    if not no_connect:
        info("Step 4: reconnecting harnesses...")
        run([sys.executable, str(ROOT / "tools/arwaky/arwaky.py"), "connect", "--all"])

    info("Step 5: verifying...")
    run([sys.executable, str(ROOT / "tools/arwaky/arwaky.py"), "check"])

    ok("Ecosystem sync complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
