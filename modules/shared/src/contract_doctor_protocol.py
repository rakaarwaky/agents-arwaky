"""Doctor-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_common_vo import ExitCode, Timestamp


class IDiagnosticRunner(ABC):
    """Capability contract for one diagnostic report."""

    @abstractmethod
    def run(self, json_mode: bool = False) -> ExitCode:
        """Run the diagnostic; return exit code."""
        return ExitCode(0)

__all__ = ['ExitCode', 'IDiagnosticRunner', 'Timestamp']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IDiagnosticRunner": IDiagnosticRunner, "Timestamp": Timestamp}
