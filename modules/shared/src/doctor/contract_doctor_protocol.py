"""Doctor-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class IDiagnosticRunner(ABC):
    """Capability contract for one diagnostic report."""

    @abstractmethod
    def run(self) -> int:
        """Run the diagnostic; return exit code."""
        raise NotImplementedError
