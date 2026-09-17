"""Check-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ICheckAggregate(ABC):
    """Aggregate over all repository-verification checks."""

    @abstractmethod
    def check(self, strict: bool = False) -> int:
        """Run every check in sequence; return exit code (1 if any errors)."""
        raise NotImplementedError
