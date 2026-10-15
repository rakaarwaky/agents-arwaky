"""Doctor-domain protocol contract (capability ABC).

Pure capability ABC: one abstract method per diagnostic operation the
runners expose. Consumers never see this method list — the aggregate
dispatches to it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_common_vo import (
    DoctorFlags,
    ExitCode,
    Timestamp,
)


class IDoctorProtocol(ABC):
    """Capability contract for the doctor diagnostic runners: one method per op."""

    @abstractmethod
    def run(self, flags: DoctorFlags | None = None) -> ExitCode:
        """Run one diagnostic pass under *flags* (``json``, ``mode``); return exit code."""
        ...


__all__ = ['DoctorFlags', 'ExitCode', 'IDoctorProtocol', 'Timestamp']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"DoctorFlags": DoctorFlags, "ExitCode": ExitCode, "IDoctorProtocol": IDoctorProtocol, "Timestamp": Timestamp}
