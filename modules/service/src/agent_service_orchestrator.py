"""Service agent orchestrator — single-execute aggregate over two subsystems.

Dispatches each ``ServiceRequest.op`` to the matching rich protocol method on
the injected control (start/stop/restart) or inspect (status/logs/help)
capability, then wraps the exit code in a ``ServiceResponse``.
"""

from __future__ import annotations

from modules.shared.src.service.contract_service_aggregate import IServiceAggregate
from modules.shared.src.service.contract_service_protocol import (
    IServiceControlProtocol,
    IServiceInspectProtocol,
)
from modules.shared.src.service.taxonomy_service_vo import (
    ServiceOp,
    ServiceRequest,
    ServiceResponse,
    ServiceTarget,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class ServiceOrchestrator(IServiceAggregate):
    """Single entry point over the service managers; dispatch happens here."""

    def __init__(
        self,
        control: IServiceControlProtocol,
        inspect: IServiceInspectProtocol,
    ) -> None:
        self._control = control
        self._inspect = inspect

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: ServiceRequest) -> ServiceResponse:
        """Route *request* to the matching subsystem; return the response."""
        op = ServiceOp(str(request.op))
        if op == "status":
            return ServiceResponse(self._inspect.status())
        if op == "start":
            return ServiceResponse(self._control.start(ServiceTarget(str(request.target))))
        if op == "stop":
            return ServiceResponse(self._control.stop(ServiceTarget(str(request.target))))
        if op == "restart":
            return ServiceResponse(self._control.restart(ServiceTarget(str(request.target))))
        if op == "logs":
            return ServiceResponse(self._inspect.logs(ServiceTarget(str(request.logs_target))))
        if op == "help":
            return ServiceResponse(self._inspect.help())
        raise ValueError(f"Unknown service op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "ServiceOrchestrator()"

__all__ = ["ServiceOrchestrator"]
