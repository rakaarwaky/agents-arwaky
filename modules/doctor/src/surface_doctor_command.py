"""Doctor surface — CLI adapters for ``aa doctor`` / ``aa status``.

Builds a typed ``DoctorRequest`` from the raw CLI tokens and calls the
aggregate's single ``execute``; the agent routes it to the right capability
method. Rendering and token parsing stay on the surface (AES406).
"""
from __future__ import annotations

import json
from collections.abc import Mapping

from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator
from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.taxonomy_common_vo import DoctorFlags, DoctorOp, DoctorRequest, ExitCode


def _flags(args: list[str]) -> DoctorFlags:
    """Convert argv flag tokens into a typed flags bag."""
    return DoctorFlags({"json": "--json" in args})


def cmd_doctor(args: list[str], orch: IDoctorAggregate) -> int:
    """aa doctor [--json] — environment + readiness diagnostics."""
    request = DoctorRequest(DoctorOp("diagnose"), flags=_flags(args))
    return int(orch.execute(request).exit_code)


def cmd_status(args: list[str], orch: IDoctorAggregate) -> int:
    """aa status [--json] — tool readiness table."""
    request = DoctorRequest(DoctorOp("readiness"), flags=_flags(args))
    return int(orch.execute(request).exit_code)


class DoctorAction(IDoctorAggregate):
    """CLI command surface for the doctor feature (owns report rendering)."""

    def __init__(self, orch: DoctorOrchestrator) -> None:
        """Hold the orchestrator reference for surface delegation."""
        self._orch = orch

    def execute(self, request: DoctorRequest) -> ExitCode:
        """Delegate the request; render any report payload before returning."""
        response = self._orch.execute(request)
        if response.report is not None:
            if (request.flags or {}).get("json"):
                print(json.dumps(response.report, indent=2, ensure_ascii=False, default=str))
            elif isinstance(response.report, Mapping):
                for key, value in response.report.items():
                    print(f"{key}: {value}")
            elif isinstance(response.report, list):
                for item in response.report:
                    print(f"- {item}")
            else:
                print(response.report)
        return response.exit_code


__all__ = ["DoctorAction", "cmd_doctor", "cmd_status"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DoctorAction": DoctorAction,
    "cmd_doctor": cmd_doctor,
    "cmd_status": cmd_status,
}
