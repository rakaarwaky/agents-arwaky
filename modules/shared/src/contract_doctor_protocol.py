"""Doctor-domain protocol contract (capability ABC)."""
from __future__ import annotations
from modules.shared.src.taxonomy_common_vo import Timestamp


from abc import ABC, abstractmethod


class IDiagnosticRunner(ABC):
    """Capability contract for one diagnostic report."""

    @abstractmethod
    def run(self, json_mode: bool = False) -> int:
        """Run the diagnostic; return exit code."""
        return None

__all__ = ['Timestamp']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"Timestamp": Timestamp}
