"""Doctor surface — CLI adapters for aa doctor / aa status (agent-layer verb, AES405)."""
from __future__ import annotations

from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator
from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate


class DoctorVerb(IDoctorAggregate):
    """Agent-layer CLI verb surface for the doctor feature (AES405 aggregate implementor)."""

    def __init__(self, orch: DoctorOrchestrator) -> None:
        self._orch = orch

    def doctor(self, json_mode: bool = False) -> int:
        return self._orch.doctor(json_mode=json_mode)

    def status(self, json_mode: bool = False) -> int:
        return self._orch.status(json_mode=json_mode)


def cmd_doctor(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa doctor — environment diagnostics."""
    return orch.doctor()


def cmd_status(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa status [--json] — tool readiness table."""
    json_mode = "--json" in args
    return orch.status(json_mode=json_mode)
