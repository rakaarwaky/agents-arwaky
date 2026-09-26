"""Doctor agent orchestrator — single-execute aggregate over the diagnostic runners.

Dispatches each ``DoctorRequest.op`` to the matching rich protocol method on
the injected runners, then wraps the outcome in a ``DoctorResponse``.
"""
from __future__ import annotations

from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.contract_doctor_protocol import IDoctorProtocol
from modules.shared.src.taxonomy_common_vo import (
    DoctorOp,
    DoctorRequest,
    DoctorResponse,
    ExitCode,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class DoctorOrchestrator(IDoctorAggregate):
    """Coordinate the two diagnostic runners (zero I/O; surface renders)."""

    def __init__(self, env_runner: IDoctorProtocol, tools_runner: IDoctorProtocol) -> None:
        """Wire the two diagnostic runners for orchestrator dispatch."""
        self._env = env_runner
        self._tools = tools_runner

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: DoctorRequest) -> DoctorResponse:
        """Route *request* to the matching protocol method; return the response."""
        op = DoctorOp(str(request.op))
        if op == "diagnose":
            rc = int(self._env.run(request.flags))
            rc |= int(self._tools.run(request.flags))
            code = ExitCode(rc)
        elif op == "readiness":
            code = self._tools.run(request.flags)
        elif op == "report":
            # Rendering lives on the surface (AES agent: zero I/O).
            code = ExitCode(0)
        else:
            raise ValueError(f"Unknown doctor op: {op}")
        return DoctorResponse(success=int(code) == 0, exit_code=code, report=request.report)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "DoctorOrchestrator()"


__all__ = ["DoctorOrchestrator", "DoctorRequest", "DoctorResponse"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DoctorOrchestrator": DoctorOrchestrator,
    "DoctorRequest": DoctorRequest,
    "DoctorResponse": DoctorResponse,
}
