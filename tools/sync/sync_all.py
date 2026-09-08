#!/usr/bin/env python3
"""One-shot ecosystem update (Python) — pengganti sync-all.sh."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from ui import info, ok, warn


def run(cmd):
    return subprocess.run(cmd).returncode


def main(argv):
    no_connect = "--no-connect" in argv
    no_build = "--no-build" in argv
    info("Running one-shot ecosystem sync...")

    failures = []
    completed_steps = []

    info("Step 1: syncing submodules...")
    if run(["git", "-C", str(ROOT), "submodule", "update", "--init", "--recursive", "vendor/", "internal/"]) != 0:
        failures.append("submodules")
    else:
        completed_steps.append("submodules")

    if not no_build:
        info("Step 2: building tools...")
        if run([sys.executable, str(ROOT / "tools/cli/arwaky.py"), "install"]) != 0:
            failures.append("install")
    else:
        completed_steps.append("install")

    info("Step 3: generating MCP config...")
    if run([sys.executable, str(ROOT / "tools/mcp/generate_config.py")]) != 0:
        failures.append("mcp-generate")
    else:
        completed_steps.append("mcp-generate")

    if not no_connect:
        info("Step 4: reconnecting harnesses...")
        if run([sys.executable, str(ROOT / "tools/cli/arwaky.py"), "connect", "--all"]) != 0:
            failures.append("connect")
    else:
        completed_steps.append("connect")

    info("Step 5: verifying...")
    if run([sys.executable, str(ROOT / "tools/cli/arwaky.py"), "check"]) != 0:
        failures.append("check")
    else:
        completed_steps.append("check")

    if failures:
        warn(f"Sync finished with failures: {', '.join(failures)}")
        warn("Completed steps that may need rollback:")
        for s in completed_steps:
            warn(f"  - {s}")
        warn("To restore submodules: git submodule foreach 'git checkout .'")
        warn("To regenerate MCP: aa mcp generate")
        warn("To reconnect harnesses: aa connect --all")
        return 1

    ok("Ecosystem sync complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
