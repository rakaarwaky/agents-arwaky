"""Check-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_check_vo import CheckExitCode, CheckScope
from modules.shared.src.taxonomy_common_vo import DocFinding


class ICheckProtocol(ABC):
    """Capability contract for one repository-verification check."""

    #: Stable CLI key for selective runs — ``docs`` | ``skill``.
    name: str = ""

    @abstractmethod
    def execute(self, scope: CheckScope) -> CheckExitCode:
        """Run this capability for *scope* strictly (every finding gates).

        Args:
            scope: Requested gate scope — ``all``, ``docs`` or ``skill``.
                The orchestrator routes the scope to the matching
                capability; one method covers every scope.

        Returns:
            Error count wrapped as the gate exit code.
        """
        ...

__all__ = ['CheckExitCode', 'CheckScope', 'DocFinding', 'ICheckProtocol']

#
# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "CheckExitCode": CheckExitCode,
    "CheckScope": CheckScope,
    "DocFinding": DocFinding,
    "ICheckProtocol": ICheckProtocol,
}
