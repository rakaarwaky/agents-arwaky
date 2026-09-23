"""Doctor surface — CLI adapters for aa doctor / aa status."""
from __future__ import annotations

from collections.abc import Mapping

from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator
from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.taxonomy_common_vo import ExitCode


class DoctorAction(IDoctorAggregate):
    """CLI command surface for the doctor feature."""

    def __init__(self, orch: DoctorOrchestrator) -> None:
        self._orch = orch

    def diagnose(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        return self._orch.diagnose(flags)

    def readiness(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        return self._orch.readiness(flags)

    def report(
        self,
        report: object,
        flags: Mapping[str, bool | str] | None = None,
    ) -> ExitCode:
        return self._orch.report(report, flags)


def _flags(args: list[str]) -> dict[str, bool]:
    return {"json": "--json" in args}


def cmd_doctor(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa doctor — environment + readiness diagnostics."""
    return orch.diagnose(_flags(args))


def cmd_status(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa status [--json] — tool readiness table."""
    return orch.readiness(_flags(args))
