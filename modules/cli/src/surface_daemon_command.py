"""Daemon surface — CLI adapters for aa anytype / aa 9router."""
from __future__ import annotations

import sys

from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_ninerouter_daemon import PodmanDaemonManager


def cmd_9router(args: list[str], orch: DaemonOrchestrator | None = None, manager: PodmanDaemonManager | None = None) -> int:
    """aa 9router <command> — start|stop|restart|status|logs|models|service-*|help."""
    mgr = manager or PodmanDaemonManager()
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
        print(f"Unknown 9router command: {action}", file=sys.stderr)
        return mgr.help()
    return handler()


def cmd_anytype(args: list[str], orch: DaemonOrchestrator | None = None, manager: AnytypeDaemonManager | None = None) -> int:
    """aa anytype <command> — start|stop|restart|status|logs|auth-*|space-*|service-*|help."""
    mgr = manager or AnytypeDaemonManager()
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
