#!/usr/bin/env python3
"""Unified service manager (Python) — pengganti service-manager.sh."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from paths import repo_root
ROOT = repo_root()
sys.path.insert(0, str(ROOT / "tools" / "lib"))

NINEROUTER = ROOT / "tools/daemons/ninerouter_daemon.py"
ANYTYPE = ROOT / "tools/daemons/anytype_daemon.py"


def run_py(script, args):
    return subprocess.run([sys.executable, str(script), *args], check=False).returncode


def cmd_status():
    print("=========== 9Router ===========")
    run_py(NINEROUTER, ["status"])
    print()
    print("=========== Anytype ===========")
    run_py(ANYTYPE, ["status"])
    return 0


def cmd_start(target="all"):
    if target in ("9router", "all"):
        run_py(NINEROUTER, ["start"])
    if target in ("anytype", "all"):
        run_py(ANYTYPE, ["start"])
    return 0


def cmd_stop(target="all"):
    if target in ("9router", "all"):
        run_py(NINEROUTER, ["stop"])
    if target in ("anytype", "all"):
        run_py(ANYTYPE, ["stop"])
    return 0


def cmd_restart(target="all"):
    if target in ("9router", "all"):
        run_py(NINEROUTER, ["restart"])
    if target in ("anytype", "all"):
        run_py(ANYTYPE, ["restart"])
    return 0


def cmd_logs(target="9router"):
    if target == "9router":
        return run_py(NINEROUTER, ["logs"])
    if target == "anytype":
        return run_py(ANYTYPE, ["logs"])
    print("Usage: aa service logs <9router|anytype>")
    return 1


def cmd_help():
    print("Usage: aa service <status|start|stop|restart|logs> [9router|anytype|all]")
    return 0


def main(argv):
    if not argv or argv[0] in ("help", "-h", "--help"):
        return cmd_help()
    action = argv[0]
    target = argv[1] if len(argv) > 1 else "all"
    if action == "status":
        return cmd_status()
    if action == "start":
        return cmd_start(target)
    if action == "stop":
        return cmd_stop(target)
    if action == "restart":
        return cmd_restart(target)
    if action == "logs":
        return cmd_logs(target)
    print(f"Unknown service command: {action}", file=sys.stderr)
    return cmd_help()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
