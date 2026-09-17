#!/usr/bin/env python3
"""Unified service manager (Python) — pengganti service-manager.sh.

AES port of tools/service/service_manager.py: body kept verbatim; only the
imports are swapped to their AES equivalents (paths) and the original
subprocess exec of the two daemon scripts is replaced by direct calls into
modules/daemon (accepted equivalent; the daemon scripts were deleted by the
AES refactor and their logic now lives in the daemon module).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root

ROOT = repo_root()

from modules.daemon.src.capabilities_daemon_podman import main as ninerouter_main
from modules.daemon.src.capabilities_daemon_anytype import main as anytype_main


def run_py(script, args):
    return subprocess.run([sys.executable, str(script), *args], check=False).returncode


def _run_ninerouter(args):
    return ninerouter_main(list(args))


def _run_anytype(args):
    return anytype_main(list(args))


def cmd_status():
    print("=========== 9Router ===========")
    _run_ninerouter(["status"])
    print()
    print("=========== Anytype ===========")
    _run_anytype(["status"])
    return 0


def cmd_start(target="all"):
    if target in ("9router", "all"):
        _run_ninerouter(["start"])
    if target in ("anytype", "all"):
        _run_anytype(["start"])
    return 0


def cmd_stop(target="all"):
    if target in ("9router", "all"):
        _run_ninerouter(["stop"])
    if target in ("anytype", "all"):
        _run_anytype(["stop"])
    return 0


def cmd_restart(target="all"):
    if target in ("9router", "all"):
        _run_ninerouter(["restart"])
    if target in ("anytype", "all"):
        _run_anytype(["restart"])
    return 0


def cmd_logs(target="9router"):
    if target == "9router":
        return _run_ninerouter(["logs"])
    if target == "anytype":
        return _run_anytype(["logs"])
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


class ServiceManager:
    """AES facade: exposes the original script verbs by their CLI names.

    The optional daemon managers in the constructor are accepted for
    composition-root wiring compatibility; verb bodies are the original
    script's top-level verb bodies (they manage the daemons directly).
    """

    def __init__(self, ninerouter=None, anytype=None) -> None:
        self._ninerouter = ninerouter
        self._anytype = anytype

    def status(self) -> int:
        return cmd_status()

    def start(self, target: str = "all") -> int:
        return cmd_start(target)

    def stop(self, target: str = "all") -> int:
        return cmd_stop(target)

    def restart(self, target: str = "all") -> int:
        return cmd_restart(target)

    def logs(self, target: str = "9router") -> int:
        return cmd_logs(target)

    def help(self) -> int:
        return cmd_help()

    def main(self, argv) -> int:
        return main(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
