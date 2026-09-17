"""Doctor surface — CLI adapters for aa doctor / aa status."""
from __future__ import annotations

from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator


def cmd_doctor(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa doctor — environment diagnostics."""
    return orch.doctor()


def cmd_status(args: list[str], orch: DoctorOrchestrator) -> int:
    """aa status [--json] — tool readiness table."""
    json_mode = "--json" in args
    return orch.status(json_mode=json_mode)
