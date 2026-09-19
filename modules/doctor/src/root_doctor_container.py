"""Doctor composition root — wires the two diagnostic runners into the orchestrator."""
from __future__ import annotations

from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator
from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner
from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner


class DoctorContainer:
    """Construct the two diagnostic runners and the orchestrator."""

    def __init__(self) -> None:
        env_runner = EnvDiagnosticRunner()
        tools_runner = ToolsDiagnosticRunner()
        self._orchestrator = DoctorOrchestrator(env_runner, tools_runner)

    @property
    def aggregate(self) -> DoctorOrchestrator:
        return self._orchestrator


def create_doctor_feature() -> DoctorOrchestrator:
    """Fully-wired doctor feature aggregate."""
    return DoctorContainer().aggregate
