"""Doctor agent orchestrator — routes doctor/status diagnostics."""
from __future__ import annotations
from modules.shared.src.taxonomy_core_vo import Timestamp


from modules.doctor.src.contract_doctor_aggregate import IDoctorAggregate
from modules.doctor.src.contract_doctor_protocol import IDiagnosticRunner


class DoctorOrchestrator(IDoctorAggregate):
    """Coordinate the two diagnostic runners.

    # Block 1: Constructor
    # Block 2: doctor/status routing
    # Block 3: (reserved)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, env_runner: IDiagnosticRunner, tools_runner: IDiagnosticRunner) -> None:
        self._env = env_runner
        self._tools = tools_runner

    # -- Block 2: doctor/status routing -------------------------------------------
    def doctor(self, json_mode: bool = False) -> int:
        rc = self._env.run(json_mode=json_mode)
        rc |= self._tools.run(json_mode=json_mode)
        return rc

    def status(self, json_mode: bool = False) -> int:
        return self._tools.run(json_mode=json_mode)

__all__ = ['Timestamp']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"Timestamp": Timestamp}
