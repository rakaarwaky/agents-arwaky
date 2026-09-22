"""Doctor-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_common_vo import ExitCode, Timestamp


class IDoctorAggregate(ABC):
    """Aggregate over all doctor diagnostic capabilities."""

    @abstractmethod
    def doctor(self, json_mode: bool = False) -> ExitCode:
        """Run the full doctor suite; return exit code."""
        return ExitCode(0)

    @abstractmethod
    def status(self, json_mode: bool = False) -> ExitCode:
        """Report tool/daemon status; return exit code."""
        return ExitCode(0)

__all__ = ['ExitCode', 'IDoctorAggregate', 'Timestamp']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IDoctorAggregate": IDoctorAggregate, "Timestamp": Timestamp}
