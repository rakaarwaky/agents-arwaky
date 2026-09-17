"""Service surface — CLI adapter for aa service."""
from __future__ import annotations

import sys

from modules.service.src.agent_service_orchestrator import ServiceOrchestrator


def cmd_service(args: list[str], orch: ServiceOrchestrator) -> int:
    """aa service <status|start|stop|restart|logs> [9router|anytype|all]."""
    if not args or args[0] in ("help", "-h", "--help"):
        return orch.help()
    action = args[0]
    target = args[1] if len(args) > 1 else "all"
    if action == "status":
        return orch.status()
    if action == "start":
        return orch.start(target)
    if action == "stop":
        return orch.stop(target)
    if action == "restart":
        return orch.restart(target)
    if action == "logs":
        return orch.logs(target)
    print(f"Unknown service command: {action}", file=sys.stderr)
    return orch.help()
