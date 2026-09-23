"""Doctor surface — CLI adapters for aa doctor / aa status."""
from __future__ import annotations

from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator
from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.taxonomy_common_vo import ExitCode


class DoctorAction(IDoctorAggregate):
    """CLI command surface for the doctor feature."""

    def __init__(self, orch: DoctorOrchestrator) -> None:
        self._orch = orch

    def doctor(self, json_mode: bool = False) -> ExitCode:
        return self._orch.doctor(json_mode=json_mode)

    def status(self, json_mode: bool = False) -> ExitCode:
        return self._orch.status(json_mode=json_mode)


def cmd_doctor(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa doctor — environment diagnostics."""
    return orch.doctor()


def cmd_status(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa status [--json] — tool readiness table."""
    json_mode = "--json" in args
    return orch.status(json_mode=json_mode)
