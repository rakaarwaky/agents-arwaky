"""Doctor agent orchestrator — routes doctor/status diagnostics."""
from __future__ import annotations

from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.contract_doctor_protocol import IDoctorProtocol
from modules.shared.src.taxonomy_common_vo import ExitCode, Timestamp


class DoctorOrchestrator(IDoctorAggregate):
    """Coordinate the two diagnostic runners.

    # Block 1: Constructor
    # Block 2: doctor/status routing
    # Block 3: (reserved)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, env_runner: IDoctorProtocol, tools_runner: IDoctorProtocol) -> None:
        self._env = env_runner
        self._tools = tools_runner

    # -- Block 2: doctor/status routing -------------------------------------------
    def doctor(self, json_mode: bool = False) -> ExitCode:
        rc = int(self._env.run(json_mode=json_mode))
        rc |= int(self._tools.run(json_mode=json_mode))
        return ExitCode(rc)

    def status(self, json_mode: bool = False) -> ExitCode:
        return self._tools.run(json_mode=json_mode)

__all__ = ['ExitCode', 'Timestamp']


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "Timestamp": Timestamp}
