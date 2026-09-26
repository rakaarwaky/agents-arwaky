"""Service surface — CLI adapter for aa service.

Builds a typed ``ServiceRequest`` from the raw CLI tokens and calls the
aggregate's single ``execute``; the agent routes it to the right capability
method. Rendering and token parsing stay on the surface (AES406).
"""
from __future__ import annotations

import sys

from modules.shared.src.contract_service_aggregate import IServiceAggregate
from modules.shared.src.taxonomy_service_vo import (
    TARGET_9ROUTER,
    TARGET_ALL,
    ServiceOp,
    ServiceRequest,
    ServiceTarget,
)

#: CLI verb → protocol method the agent dispatches to.
_SERVICE_OPS: dict[str, str] = {
    "status": "status",
    "start": "start",
    "stop": "stop",
    "restart": "restart",
    "logs": "logs",
    "help": "help",
}


def cmd_service(args: list[str], orch: IServiceAggregate) -> int:
    """aa service <status|start|stop|restart|logs> [9router|anytype|all]."""
    if not args or args[0] in ("help", "-h", "--help"):
        return int(orch.execute(ServiceRequest(ServiceOp("help"))))
    action = args[0]
    if action not in _SERVICE_OPS:
        print(f"Unknown service command: {action}", file=sys.stderr)
        int(orch.execute(ServiceRequest(ServiceOp("help"))))
        return 1
    target = ServiceTarget(args[1] if len(args) > 1 else "all")
    # `logs` defaults to 9router when no explicit target is given.
    logs_target = ServiceTarget(str(target)) if len(args) > 1 else TARGET_9ROUTER
    request = ServiceRequest(ServiceOp(action), target=target, logs_target=logs_target)
    return int(orch.execute(request))


class ServiceAction(IServiceAggregate):
    """Aggregate implementor wrapping another aggregate (surface-layer facade)."""

    def __init__(self, agg: IServiceAggregate) -> None:
        """Store the underlying service aggregate for delegation."""
        self._agg = agg

    def execute(self, request: ServiceRequest) -> int:
        """Delegate the request to the wrapped aggregate unchanged."""
        return int(self._agg.execute(request))


__all__ = ["ServiceAction", "cmd_service"]
