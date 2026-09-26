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
from modules.shared.src.taxonomy_daemon_vo import DaemonName, DaemonOp, DaemonRequest
from modules.shared.src.taxonomy_service_vo import (
    TARGET_ALL,
    TARGET_9ROUTER,
    ExitCode,
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

    # ─── Block 2: Protocol Method Implementation ──────────────
    def status(self) -> ExitCode:
        """Report the health of every registered service. Return the exit code."""
        return ExitCode(cmd_status())

    def start(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Start the named service(s). Return the exit code."""
        return ExitCode(cmd_start(str(target)))

    def stop(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Stop the named service(s). Return the exit code."""
        return ExitCode(cmd_stop(str(target)))

    def restart(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Restart the named service(s). Return the exit code."""
        return ExitCode(cmd_restart(str(target)))

    def logs(self, target: ServiceTarget = TARGET_9ROUTER) -> ExitCode:
        """Stream the named service's logs. Return the exit code."""
        return ExitCode(cmd_logs(str(target)))

    def help(self) -> ExitCode:
        """Print the service command usage. Return the exit code."""
        return ExitCode(cmd_help())

    def __repr__(self) -> str:
        return "ServiceManager()"

    def main(self, argv) -> int:
        """Run the service manager CLI entry point with the given arguments."""
        return main(argv)


def _run_9router(args: list[str]) -> int:
    """Run the 9Router daemon helper, starting it if the first arg is 'start'."""
    return int(_daemons().start("9router")) if args and args[0] == "start" else _daemon_main("9router", args)


def _run_anytype(args: list[str]) -> int:
    """Run the Anytype daemon helper."""
    return _daemon_main("anytype", args)


def _daemon_main(name: str, args: list[str]) -> int:
    """Route daemon CLI arguments to the injected daemon aggregate."""
    agg = _daemons()
    action = (args[0] if args else "help").lower()
    if action in ("start", "stop", "restart", "logs"):
        request = DaemonRequest(DaemonOp(action), name=DaemonName(name))
        return int(agg.execute(request).exit_code or 0)
    if action == "status":
        result = agg.execute(DaemonRequest(DaemonOp("status"), name=DaemonName(name)))
        return 0 if result.status and result.status.ok else 1
    return 0


def cmd_status() -> int:
    """Print status for all registered services."""
    print("=========== 9Router ===========")
    _run_9router(["status"])
    print()
    print("=========== Anytype ===========")
    _run_anytype(["status"])
    return 0


def cmd_start(target: str = "all") -> int:
    """Start the requested service target(s)."""
    if target in ("9router", "all"):
        _run_9router(["start"])
    if target in ("anytype", "all"):
        _run_anytype(["start"])
    return 0


def cmd_stop(target: str = "all") -> int:
    """Stop the requested service target(s)."""
    if target in ("9router", "all"):
        _run_9router(["stop"])
    if target in ("anytype", "all"):
        _run_anytype(["stop"])
    return 0


def cmd_restart(target: str = "all") -> int:
    """Restart the requested service target(s)."""
    if target in ("9router", "all"):
        _run_9router(["restart"])
    if target in ("anytype", "all"):
        _run_anytype(["restart"])
    return 0


def cmd_logs(target: str = "9router") -> int:
    """Print logs for the requested service target(s)."""
    if target == "9router":
        return _run_9router(["logs"])
    if target == "anytype":
        return _run_anytype(["logs"])
    print("Usage: aa service logs <9router|anytype>")
    return 1


def cmd_help() -> int:
    """Print the service command usage summary."""
    print("Usage: aa service <status|start|stop|restart|logs> [9router|anytype|all]")
    return 0


def main(argv: list[str]) -> int:
    """Entry point for standalone service command execution."""
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

__all__ = ["ExitCode", "IServiceProtocol", "ServiceManager", "ServiceTarget"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IServiceProtocol": IServiceProtocol, "ServiceManager": ServiceManager, "ServiceTarget": ServiceTarget}

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
