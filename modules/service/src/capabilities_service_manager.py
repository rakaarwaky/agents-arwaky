#!/usr/bin/env python3
"""Unified service manager (Python) — pengganti service-manager.sh.

AES port of tools/service/service_manager.py: verb bodies kept; the original
subprocess exec of the two daemon scripts is replaced by direct calls into
modules/daemon. The daemon managers are resolved via the daemon feature
aggregate (composition root) and injected; the module-level cmd_* functions
fall back to a lazily-built aggregate only when called standalone.
"""
from __future__ import annotations

import sys

from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_service_protocol import IServiceManager
from modules.shared.src.taxonomy_service_vo import ExitCode, ServiceTarget

_DAEMON_AGGREGATE: IDaemonAggregate | None = None


def _daemons() -> IDaemonAggregate:
    """Daemon aggregate cache: set by the service root container at construction."""
    if _DAEMON_AGGREGATE is None:
        raise RuntimeError(
            "ServiceManager has no daemon aggregate injected; use "
            "create_service_feature() (root composition) instead of a bare constructor call."
        )
    return _DAEMON_AGGREGATE


# ─── Block 1: Class Definition & Constructor ──────────────
class ServiceManager(IServiceManager):
    """AES facade: exposes the original script verbs by their CLI names.

    The optional daemon aggregate in the constructor is accepted for
    composition-root wiring; verb bodies route through it.
    """

    def __init__(self, daemons: IDaemonAggregate | None = None) -> None:
        global _DAEMON_AGGREGATE
        if daemons is not None:
            _DAEMON_AGGREGATE = daemons
        self._daemons = daemons

    @property
    def aggregate(self) -> IDaemonAggregate:
        """Return the injected daemon aggregate (composition-time wiring)."""
        return self._daemons

    def status(self) -> ExitCode:
        return ExitCode(cmd_status())

    # ─── Block 2: Protocol ABC Method Implementation ──────────

    def start(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        return ExitCode(cmd_start(str(target)))

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def stop(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        return ExitCode(cmd_stop(str(target)))

    def restart(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        return ExitCode(cmd_restart(str(target)))

    def logs(self, target: ServiceTarget = ServiceTarget("omniroute")) -> ExitCode:
        return ExitCode(cmd_logs(str(target)))

    def help(self) -> ExitCode:
        return ExitCode(cmd_help())

    def main(self, argv) -> int:
        return main(argv)


def _run_omniroute(args: list[str]) -> int:
    return _daemons().start_daemon("omniroute") if args and args[0] == "start" else _daemon_main("omniroute", args)


def _run_anytype(args: list[str]) -> int:
    return _daemon_main("anytype", args)


def _daemon_main(name: str, args: list[str]) -> int:
    agg = _daemons()
    verb = (args[0] if args else "help").lower()
    if verb == "start":
        return agg.start_daemon(name)
    if verb == "stop":
        return agg.stop_daemon(name)
    if verb == "restart":
        return agg.restart_daemon(name)
    if verb == "logs":
        return agg.logs_daemon(name)
    if verb == "status":
        agg.status_daemon(name)
        return 0
    return 0


def cmd_status() -> int:
    print("=========== OmniRoute ===========")
    _run_omniroute(["status"])
    print()
    print("=========== Anytype ===========")
    _run_anytype(["status"])
    return 0


def cmd_start(target: str = "all") -> int:
    if target in ("omniroute", "all"):
        _run_omniroute(["start"])
    if target in ("anytype", "all"):
        _run_anytype(["start"])
    return 0


def cmd_stop(target: str = "all") -> int:
    if target in ("omniroute", "all"):
        _run_omniroute(["stop"])
    if target in ("anytype", "all"):
        _run_anytype(["stop"])
    return 0


def cmd_restart(target: str = "all") -> int:
    if target in ("omniroute", "all"):
        _run_omniroute(["restart"])
    if target in ("anytype", "all"):
        _run_anytype(["restart"])
    return 0


def cmd_logs(target: str = "omniroute") -> int:
    if target == "omniroute":
        return _run_omniroute(["logs"])
    if target == "anytype":
        return _run_anytype(["logs"])
    print("Usage: aa service logs <omniroute|anytype>")
    return 1


def cmd_help() -> int:
    print("Usage: aa service <status|start|stop|restart|logs> [omniroute|anytype|all]")
    return 0


def main(argv: list[str]) -> int:
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

__all__ = ['ExitCode', 'IServiceManager', 'ServiceManager', 'ServiceTarget']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IServiceManager": IServiceManager, "ServiceManager": ServiceManager, "ServiceTarget": ServiceTarget}

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


