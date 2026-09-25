"""Doctor surface — CLI adapters for aa doctor / aa status."""
from __future__ import annotations

import json
from collections.abc import Mapping

from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator
from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.taxonomy_common_vo import ExitCode


class DoctorAction(IDoctorAggregate):
    """CLI command surface for the doctor feature (owns report rendering)."""

    def __init__(self, orch: DoctorOrchestrator) -> None:
        """Hold the orchestrator reference for surface method delegation."""
        self._orch = orch

    def diagnose(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        """Delegate diagnosis to the orchestrator (no I/O at this layer)."""
        return self._orch.diagnose(flags)

    def readiness(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        """Delegate readiness check to the orchestrator (no I/O at this layer)."""
        return self._orch.readiness(flags)

    def report(
        self,
        report: object,
        flags: Mapping[str, bool | str] | None = None,
    ) -> ExitCode:
        """Render *report* as JSON or text (surface owns I/O)."""
        if (flags or {}).get("json"):
            print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
            return ExitCode(0)
        if isinstance(report, Mapping):
            for key, value in report.items():
                print(f"{key}: {value}")
        elif isinstance(report, list):
            for item in report:
                print(f"- {item}")
        else:
            print(report)
        return ExitCode(0)


def _flags(args: list[str]) -> dict[str, bool]:
    """Convert argv flag tokens into a boolean flags dict."""
    return {"json": "--json" in args}


def cmd_doctor(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa doctor — environment + readiness diagnostics."""
    return orch.diagnose(_flags(args))


def cmd_status(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa status [--json] — tool readiness table."""
    return orch.readiness(_flags(args))
