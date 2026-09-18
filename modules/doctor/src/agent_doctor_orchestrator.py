"""Doctor agent orchestrator — routes doctor/status diagnostics."""
from __future__ import annotations

from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner
from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner
from modules.doctor.src.contract_doctor_protocol import IDiagnosticRunner


class DoctorOrchestrator:
    """Coordinate the two diagnostic runners.

    # Block 1: Constructor
    # Block 2: doctor/status routing
    # Block 3: (reserved)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, env_runner: EnvDiagnosticRunner, tools_runner: ToolsDiagnosticRunner) -> None:
        self._env = env_runner
        self._tools = tools_runner

    # -- Block 2: doctor/status routing -------------------------------------------
    def doctor(self) -> int:
        return self._env.run()

    def status(self, json_mode: bool = False) -> int:
        return self._tools.run(json_mode=json_mode)
