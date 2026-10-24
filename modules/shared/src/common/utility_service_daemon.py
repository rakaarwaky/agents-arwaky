"""Service daemon-routing helpers (AES utility layer).

Stateless CLI-verb dispatch for the two service capabilities
(``ServiceControl`` and ``ServiceInspect``) — routes start/stop/restart/
status/logs/help arguments through the injected daemon aggregate, holding no
capability state. Shared here so no capability imports a sibling capability
(AES201).
"""
from __future__ import annotations

from modules.shared.src.daemon.taxonomy_daemon_vo import (
    DaemonName,
    DaemonOp,
    DaemonRequest,
)

__all__ = [
    "cmd_help",
    "cmd_logs",
    "cmd_restart",
    "cmd_start",
    "cmd_status",
    "cmd_stop",
    "daemon_main",
    "set_daemon_aggregate",
]


_DAEMON_AGGREGATE: object | None = None
# Keep the aggregate reference loosely typed (contract import is forbidden
# in the utility layer per AES201; the aggregate is injected by the root
# container and routed through at call time).


def set_daemon_aggregate(agg) -> None:
    """Record the daemon aggregate for later routing calls."""
    global _DAEMON_AGGREGATE
    _DAEMON_AGGREGATE = agg


def _daemons():
    """The daemon aggregate; raise when no root container injected one."""
    if _DAEMON_AGGREGATE is None:
        raise RuntimeError(
            "Service capability has no daemon control injected; use "
            "create_service_feature() (root composition) instead of a bare "
            "constructor call."
        )
    return _DAEMON_AGGREGATE


def daemon_main(name: str, args: list[str]) -> int:
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


def _run_omniroute(args: list[str]) -> int:
    """Run the OmniRoute daemon helper."""
    return daemon_main("omniroute", args)


def _run_anytype(args: list[str]) -> int:
    """Run the Anytype daemon helper."""
    return daemon_main("anytype", args)


def cmd_status() -> int:
    """Print status for all registered services."""
    print("=========== OmniRoute ===========")
    _run_omniroute(["status"])
    print()
    print("=========== Anytype ===========")
    _run_anytype(["status"])
    return 0


def cmd_start(target: str = "all") -> int:
    """Start the requested service target(s)."""
    if target in ("omniroute", "all"):
        _run_omniroute(["start"])
    if target in ("anytype", "all"):
        _run_anytype(["start"])
    return 0


def cmd_stop(target: str = "all") -> int:
    """Stop the requested service target(s)."""
    if target in ("omniroute", "all"):
        _run_omniroute(["stop"])
    if target in ("anytype", "all"):
        _run_anytype(["stop"])
    return 0


def cmd_restart(target: str = "all") -> int:
    """Restart the requested service target(s)."""
    if target in ("omniroute", "all"):
        _run_omniroute(["restart"])
    if target in ("anytype", "all"):
        _run_anytype(["restart"])
    return 0


def cmd_logs(target: str = "omniroute") -> int:
    """Print logs for the requested service target(s)."""
    if target == "omniroute":
        return _run_omniroute(["logs"])
    if target == "anytype":
        return _run_anytype(["logs"])
    print("Usage: aa service logs <omniroute|anytype>")
    return 1


def cmd_help() -> int:
    """Print the service command usage summary."""
    print("Usage: aa service <status|start|stop|restart|logs> [omniroute|anytype|all]")
    return 0
