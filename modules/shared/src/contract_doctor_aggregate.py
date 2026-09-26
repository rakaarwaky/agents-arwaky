"""Doctor-domain aggregate contract (agent orchestrator ABC).

Single entry point over the doctor feature: the surface, root and CLI call
``execute`` with a request and get a response back. The agent behind the
aggregate routes each ``op`` to the matching protocol method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_common_vo import (
    DoctorRequest,
    DoctorResponse,
    ExitCode,
    Timestamp,
)


class IDoctorAggregate(ABC):
    """Single entry point over doctor diagnostics; the agent dispatches internally."""

    @abstractmethod
    def execute(self, request: DoctorRequest) -> DoctorResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...


__all__ = ['DoctorRequest', 'DoctorResponse', 'ExitCode', 'IDoctorAggregate', 'Timestamp']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DoctorRequest": DoctorRequest,
    "DoctorResponse": DoctorResponse,
    "ExitCode": ExitCode,
    "IDoctorAggregate": IDoctorAggregate,
    "Timestamp": Timestamp,
}
