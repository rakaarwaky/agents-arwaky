"""Daemon surface — CLI adapters for aa anytype / aa omniroute.

The concrete daemon managers are constructed by the composition root (root layer)
and injected into these verbs; this module stays free of root/capability imports.
"""
from __future__ import annotations

import sys
from typing import Callable

from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.contract_daemon_aggregate import IDaemonAggregate
from modules.daemon.src.contract_daemon_protocol import IDaemonManager

#: factory name -> manager callable, injected by the composition root.
_MANAGER_FACTORY: dict[str, Callable[[], IDaemonManager]] = {}


def register_manager_factory(name: str, factory: Callable[[], IDaemonManager]) -> None:
    """Register a manager factory for *name* (composition root only)."""
    _MANAGER_FACTORY[name] = factory


def _manager(name: str) -> IDaemonManager:
    factory = _MANAGER_FACTORY.get(name)
    if factory is None:
        raise RuntimeError(f"no daemon manager factory registered for {name!r}")
    return factory()


def cmd_omniroute(args: list[str], orch: DaemonOrchestrator | None = None, manager: IDaemonManager | None = None) -> int:
    """aa omniroute <command> — start|stop|restart|status|logs|models|service-*|help."""
    mgr = manager or _manager("omniroute")
    if not args or args[0] in ("help", "-h", "--help"):
        return mgr.help()
    action = args[0]
    dispatch = {
        "start": mgr.start,
        "stop": mgr.stop,
        "restart": mgr.restart,
        "status": lambda: mgr.status(),
        "logs": mgr.logs,
        "models": mgr.models,
        "service-install": mgr.service_install,
        "service-status": mgr.service_status,
        "service-uninstall": mgr.service_uninstall,
    }
    handler = dispatch.get(action)
    if not handler:
        print(f"Unknown omniroute command: {action}", file=sys.stderr)
        return mgr.help()
    return handler()


def cmd_anytype(args: list[str], orch: DaemonOrchestrator | None = None, manager: IDaemonManager | None = None) -> int:
    """aa anytype <command> — start|stop|restart|status|logs|auth-*|space-*|service-*|help."""
    mgr = manager or _manager("anytype")
    if not args or args[0] in ("help", "-h", "--help"):
        return mgr.help()
    action = args[0]
    rest = args[1:]
    dispatch = {
        "start": lambda: mgr.start(),
        "stop": lambda: mgr.stop(),
        "restart": lambda: mgr.restart(),
        "status": lambda: mgr.status(),
        "logs": lambda: mgr.logs(),
        "auth-create": lambda: mgr.auth_create(rest[0] if rest else "agent"),
        "auth-key": lambda: mgr.auth_key(rest[0] if rest else "arwaky-agent-key"),
        "space-join": lambda: mgr.space_join(rest[0] if rest else ""),
        "space-list": lambda: mgr.space_list(),
        "service-install": lambda: mgr.service_install(),
        "service-status": lambda: mgr.service_status(),
    }
    handler = dispatch.get(action)
    if handler:
        return handler()
    print(f"Unknown anytype command: {action}", file=sys.stderr)
    return mgr.help()


class DaemonVerb(IDaemonAggregate):
    """Agent-layer verb surface for the daemon feature (AES405 aggregate implementor)."""

    def __init__(self, agg: IDaemonAggregate) -> None:
        self._agg = agg

    def start_daemon(self, name: str) -> int:
        return self._agg.start_daemon(name)

    def stop_daemon(self, name: str) -> int:
        return self._agg.stop_daemon(name)

    def status_daemon(self, name: str):
        return self._agg.status_daemon(name)

    def logs_daemon(self, name: str) -> int:
        return self._agg.logs_daemon(name)

    def restart_daemon(self, name: str) -> int:
        return self._agg.restart_daemon(name)
