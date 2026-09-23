"""Check-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_check_vo import CheckExitCode
from modules.shared.src.taxonomy_common_vo import DocFinding


class ICheckAggregate(ABC):
    """Aggregate over all repository-verification checks."""

    @abstractmethod
    def check(self, only: str | None = None) -> CheckExitCode:
        """Run checks in sequence strictly (every finding gates); return exit code.

        Args:
            only: Run a single capability by runner ``name`` (``docs`` | ``skill``);
                ``None``/``"all"`` runs every registered runner.
        """
        return None

__all__ = ['CheckExitCode', 'DocFinding']

#
# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"CheckExitCode": CheckExitCode, "DocFinding": DocFinding}
