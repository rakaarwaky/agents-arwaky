"""Doctor agent orchestrator — routes diagnose/readiness/report."""
from __future__ import annotations

import json
from collections.abc import Mapping

from modules.shared.src.contract_doctor_aggregate import IDoctorAggregate
from modules.shared.src.contract_doctor_protocol import IDoctorProtocol
from modules.shared.src.taxonomy_common_vo import ExitCode, Timestamp


class DoctorOrchestrator(IDoctorAggregate):
    """Coordinate the two diagnostic runners.

    # Block 1: Constructor
    # Block 2: diagnose/readiness/report routing
    # Block 3: (reserved)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, env_runner: IDoctorProtocol, tools_runner: IDoctorProtocol) -> None:
        self._env = env_runner
        self._tools = tools_runner

    # -- Block 2: diagnose/readiness/report routing --------------------------------
    def diagnose(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        rc = int(self._env.execute(flags))
        rc |= int(self._tools.execute(flags))
        return ExitCode(rc)

    def readiness(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        return self._tools.execute(flags)

    def report(
        self,
        report: object,
        flags: Mapping[str, bool | str] | None = None,
    ) -> ExitCode:
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

__all__ = ['ExitCode', 'Timestamp']


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "Timestamp": Timestamp}
