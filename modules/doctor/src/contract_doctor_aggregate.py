"""Doctor-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations
from modules.shared.src.taxonomy_core_vo import Timestamp



from abc import ABC, abstractmethod


class IDoctorAggregate(ABC):
    """Aggregate over all doctor diagnostic capabilities."""

    @abstractmethod
    def doctor(self, json_mode: bool = False) -> int:
        """Run the full doctor suite; return exit code."""
        return None

    @abstractmethod
    def status(self, json_mode: bool = False) -> int:
        """Report tool/daemon status; return exit code."""
        return None

__all__ = ['Timestamp']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"Timestamp": Timestamp}
