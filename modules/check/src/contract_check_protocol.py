"""Check-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ICheckRunner(ABC):
    """Capability contract for one repository-verification check."""

    @abstractmethod
    def run(self, strict: bool = False) -> int:
        """Run the check; return the number of errors found."""
        raise NotImplementedError
