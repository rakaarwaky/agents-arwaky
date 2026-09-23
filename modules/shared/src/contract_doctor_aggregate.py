"""Doctor-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

from modules.shared.src.taxonomy_common_vo import ExitCode, Timestamp


class IDoctorAggregate(ABC):
    """Aggregate over all doctor diagnostic capabilities."""

    @abstractmethod
    def diagnose(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        """Run the full environment + readiness diagnosis; return exit code."""
        ...
    @abstractmethod
    def readiness(self, flags: Mapping[str, bool | str] | None = None) -> ExitCode:
        """Report tool readiness rows; return exit code."""
        ...
    @abstractmethod
    def report(
        self,
        report: object,
        flags: Mapping[str, bool | str] | None = None,
    ) -> ExitCode:
        """Render *report* as text, or JSON under the ``json`` flag."""
        ...

__all__ = ['ExitCode', 'IDoctorAggregate', 'Timestamp']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IDoctorAggregate": IDoctorAggregate, "Timestamp": Timestamp}
