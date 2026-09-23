"""Doctor-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_common_vo import (
    DoctorFlags,
    DoctorReport,
    ExitCode,
    Timestamp,
)


class IDoctorAggregate(ABC):
    """Aggregate over all doctor diagnostic capabilities."""

    @abstractmethod
    def diagnose(self, flags: DoctorFlags | None = None) -> ExitCode:
        """Run the full environment + readiness diagnosis; return exit code."""
        ...
    @abstractmethod
    def readiness(self, flags: DoctorFlags | None = None) -> ExitCode:
        """Report tool readiness rows; return exit code."""
        ...
    @abstractmethod
    def report(
        self,
        report: DoctorReport,
        flags: DoctorFlags | None = None,
    ) -> ExitCode:
        """Render *report* as text, or JSON under the ``json`` flag."""
        ...

__all__ = ['DoctorFlags', 'DoctorReport', 'ExitCode', 'IDoctorAggregate', 'Timestamp']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DoctorFlags": DoctorFlags,
    "DoctorReport": DoctorReport,
    "ExitCode": ExitCode,
    "IDoctorAggregate": IDoctorAggregate,
    "Timestamp": Timestamp,
}
