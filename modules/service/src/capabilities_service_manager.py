#!/usr/bin/env python3
"""Unified service manager (Python) — pengganti service-manager.sh.

AES port of tools/service/service_manager.py: action bodies kept; the original
subprocess exec of the two daemon scripts is replaced by direct calls into
modules/daemon. The daemon managers are resolved via the daemon feature
aggregate (composition root) and injected; the module-level cmd_* functions
fall back to a lazily-built aggregate only when called standalone.
"""
from __future__ import annotations

import sys

from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_service_protocol import IServiceProtocol
from modules.shared.src.taxonomy_service_vo import (
    TARGET_ALL,
    TARGET_OMNIROUTE,
    ExitCode,
    ServiceOp,
    ServiceTarget,
)

_DAEMON_AGGREGATE: IDaemonAggregate | None = None


def _daemons() -> IDaemonAggregate:
    """Daemon control surface: set by the service root container at construction."""
    if _DAEMON_AGGREGATE is None:
        raise RuntimeError(
            "ServiceManager has no daemon control injected; use "
            "create_service_feature() (root composition) instead of a bare constructor call."
        )
    return _DAEMON_AGGREGATE


# ─── Block 1: Class Definition & Constructor ──────────────
class ServiceManager(IServiceProtocol):
    """AES facade: exposes the original script actions by their CLI names.

    The optional daemon aggregate in the constructor is accepted for
    composition-root wiring; action bodies route through it.
    """

    def __init__(self, daemons: IDaemonAggregate | None = None) -> None:
        global _DAEMON_AGGREGATE
        if daemons is not None:
            _DAEMON_AGGREGATE = daemons
        self._daemons = daemons

    @property
    def aggregate(self) -> IDaemonAggregate | None:
        """Return the injected daemon aggregate (composition-time wiring)."""
        return self._daemons

    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def execute(self, op: ServiceOp, unit: ServiceTarget = TARGET_ALL) -> ExitCode:
        if op == "status":
            return self.status()
        if op == "start":
            return self.start(ServiceTarget(str(unit)))
        if op == "stop":
            return self.stop(ServiceTarget(str(unit)))
        if op == "restart":
            return self.restart(ServiceTarget(str(unit)))
        if op == "logs":
            return self.logs(ServiceTarget(str(unit)) if str(unit) != "all" else ServiceTarget("omniroute"))
        if op == "help":
            return self.help()
        raise ValueError(f"Unknown service op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def __repr__(self) -> str:
        return "ServiceManager()"

    def status(self) -> ExitCode:
        return ExitCode(cmd_status())

    def start(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        return ExitCode(cmd_start(str(target)))

    def stop(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        return ExitCode(cmd_stop(str(target)))

    def restart(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        return ExitCode(cmd_restart(str(target)))

    def logs(self, target: ServiceTarget = TARGET_OMNIROUTE) -> ExitCode:
        return ExitCode(cmd_logs(str(target)))

    def help(self) -> ExitCode:
        return ExitCode(cmd_help())

    def main(self, argv) -> int:
        return main(argv)


def _run_omniroute(args: list[str]) -> int:
    return int(_daemons().start("omniroute")) if args and args[0] == "start" else _daemon_main("omniroute", args)


def _run_anytype(args: list[str]) -> int:
    return _daemon_main("anytype", args)


def _daemon_main(name: str, args: list[str]) -> int:
    agg = _daemons()
    action = (args[0] if args else "help").lower()
    if action == "start":
        return int(agg.start(name))
    if action == "stop":
        return int(agg.stop(name))
    if action == "restart":
        return int(agg.restart(name))
    if action == "logs":
        return int(agg.logs(name))
    if action == "status":
        agg.status(name)
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
    cmd_help()
    return 1

__all__ = ['ExitCode', 'IServiceProtocol', 'ServiceManager', 'ServiceOp', 'ServiceTarget']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IServiceProtocol": IServiceProtocol, "ServiceManager": ServiceManager, "ServiceOp": ServiceOp, "ServiceTarget": ServiceTarget}

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


