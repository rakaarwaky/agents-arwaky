"""Service agent orchestrator — single-execute aggregate over the service manager.

Dispatches each ``ServiceRequest.op`` to the matching rich protocol method on
the injected manager, then wraps the exit code in a ``ServiceResponse``.
"""
from __future__ import annotations

from modules.shared.src.contract_service_aggregate import IServiceAggregate
from modules.shared.src.contract_service_protocol import IServiceProtocol
from modules.shared.src.taxonomy_service_vo import (
    ServiceOp,
    ServiceRequest,
    ServiceResponse,
    ServiceTarget,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class ServiceOrchestrator(IServiceAggregate):
    """Single entry point over the service manager; dispatch happens here."""

    def __init__(self, manager: IServiceProtocol) -> None:
        self._manager = manager

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: ServiceRequest) -> ServiceResponse:
        """Route *request* to the matching protocol method; return the response."""
        op = ServiceOp(str(request.op))
        if op == "status":
            return ServiceResponse(self._manager.status())
        if op == "start":
            return ServiceResponse(self._manager.start(ServiceTarget(str(request.target))))
        if op == "stop":
            return ServiceResponse(self._manager.stop(ServiceTarget(str(request.target))))
        if op == "restart":
            return ServiceResponse(self._manager.restart(ServiceTarget(str(request.target))))
        if op == "logs":
            return ServiceResponse(self._manager.logs(ServiceTarget(str(request.logs_target))))
        if op == "help":
            return ServiceResponse(self._manager.help())
        raise ValueError(f"Unknown service op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "ServiceOrchestrator()"


__all__ = ["ServiceOrchestrator", "ServiceRequest", "ServiceResponse"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ServiceOrchestrator": ServiceOrchestrator,
    "ServiceRequest": ServiceRequest,
    "ServiceResponse": ServiceResponse,
}
