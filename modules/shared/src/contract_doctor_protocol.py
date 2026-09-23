"""Doctor-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_common_vo import DoctorFlags, ExitCode, Timestamp


class IDoctorProtocol(ABC):
    """Capability contract for one diagnostic report."""

    @abstractmethod
    def execute(self, flags: DoctorFlags | None = None) -> ExitCode:
        """Run one diagnostic pass under *flags* (``json``, ``mode``); return exit code."""
        ...

__all__ = ['DoctorFlags', 'ExitCode', 'IDoctorProtocol', 'Timestamp']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"DoctorFlags": DoctorFlags, "ExitCode": ExitCode, "IDoctorProtocol": IDoctorProtocol, "Timestamp": Timestamp}
