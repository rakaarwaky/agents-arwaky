"""Daemon surface — CLI adapters for aa anytype / aa 9router.

The concrete daemon managers are constructed by the composition root (root layer)
and injected into these actions; this module stays free of root/capability imports.
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_daemon_protocol import IDaemonProtocol
from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonStatus,
    DaemonUnit,
    ExitCode,
)

#: factory name -> manager callable, injected by the composition root.
_MANAGER_FACTORY: dict[str, Callable[[], IDaemonProtocol]] = {}

#: unit ops that need the manager's unit filename.
_UNIT_OPS = frozenset({"install_unit", "remove_unit", "unit_status"})

#: CLI verb -> protocol op.
_OPS: dict[str, str] = {
    "start": "start",
    "stop": "stop",
    "restart": "restart",
    "status": "status",
    "logs": "logs",
    "help": "help",
    "models": "models",
    "auth-create": "auth-create",
    "auth-key": "auth-key",
    "space-join": "space-join",
    "space-list": "space-list",
    "service-install": "install_unit",
    "service-status": "unit_status",
    "service-uninstall": "remove_unit",
}


def register_manager_factory(name: str, factory: Callable[[], IDaemonProtocol]) -> None:
    """Register a manager factory for *name* (composition root only)."""
    _MANAGER_FACTORY[name] = factory


def _manager(name: str) -> IDaemonProtocol:
    factory = _MANAGER_FACTORY.get(name)
    if factory is None:
        raise RuntimeError(f"no daemon manager factory registered for {name!r}")
    return factory()


def _dispatch(
    mgr: IDaemonProtocol,
    args: list[str],
    *,
    unit: str,
    label: str,
) -> int:
    if not args or args[0] in ("help", "-h", "--help"):
        return int(mgr.execute("help"))
    action = args[0]
    rest = args[1:]
    op = _OPS.get(action)
    if op is None:
        print(f"Unknown {label} command: {action}", file=sys.stderr)
        return int(mgr.execute("help"))
    name = rest[0] if rest else None
    result = mgr.execute(op, name=name, unit=unit if op in _UNIT_OPS else None)
    if isinstance(result, DaemonStatus):
        return 0 if result.ok else 1
    return int(result)


def cmd_9router(args: list[str], orch: DaemonOrchestrator | None = None, manager: IDaemonProtocol | None = None) -> int:
    """aa 9router <command> — start|stop|restart|status|logs|models|service-*|help."""
    mgr = manager or _manager("9router")
    return _dispatch(mgr, args, unit="9router.service", label="9router")


def cmd_anytype(args: list[str], orch: DaemonOrchestrator | None = None, manager: IDaemonProtocol | None = None) -> int:
    """aa anytype <command> — start|stop|restart|status|logs|auth-*|space-*|service-*|help."""
    mgr = manager or _manager("anytype")
    return _dispatch(mgr, args, unit="anytype-daemon.service", label="anytype")


class DaemonAction(IDaemonAggregate):
    """Agent-layer action surface for the daemon feature (AES405 aggregate implementor)."""

    def __init__(self, agg: IDaemonAggregate) -> None:
        self._agg = agg

    def list_known(self) -> tuple[DaemonName, ...]:
        """Names of the daemons this action surface can route to."""
        return self._agg.list_known()

    def start(self, name: DaemonName) -> ExitCode:
        """Start the named daemon; delegates to the underlying aggregate."""
        return self._agg.start(name)

    def stop(self, name: DaemonName) -> ExitCode:
        """Stop the named daemon; delegates to the underlying aggregate."""
        return self._agg.stop(name)

    def restart(self, name: DaemonName) -> ExitCode:
        """Restart the named daemon; delegates to the underlying aggregate."""
        return self._agg.restart(name)

    def status(self, name: DaemonName) -> DaemonStatus:
        """Query daemon state; delegates to the underlying aggregate."""
        return self._agg.status(name)

    def logs(self, name: DaemonName) -> ExitCode:
        """Tail daemon logs; delegates to the underlying aggregate."""
        return self._agg.logs(name)

    def install_unit(self, unit: DaemonUnit) -> ExitCode:
        """Install the systemd user unit; delegates to the underlying aggregate."""
        return self._agg.install_unit(unit)

    def remove_unit(self, unit: DaemonUnit) -> ExitCode:
        """Remove the systemd user unit; delegates to the underlying aggregate."""
        return self._agg.remove_unit(unit)

    def unit_status(self, unit: DaemonUnit) -> ExitCode:
        """Report systemd state of *unit*; delegates to the underlying aggregate."""
        return self._agg.unit_status(unit)
