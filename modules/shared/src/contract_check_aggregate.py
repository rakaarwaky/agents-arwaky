"""Check-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_check_vo import (
    CheckExitCode,
    CheckOnly,
    CheckSummary,
)
from modules.shared.src.taxonomy_common_vo import DocFinding, DocFindings


class ICheckAggregate(ABC):
    """Aggregate over all repository-verification checks."""

    @abstractmethod
    def check(self, only: CheckOnly | None = None) -> CheckExitCode:
        """Run checks in sequence strictly (every finding gates); return exit code.

        Args:
            only: Run a single capability by runner ``name`` (``docs`` | ``skill``);
                ``None``/``"all"`` runs every registered runner.
        """
        ...

    @abstractmethod
    def check_docs(self) -> CheckExitCode:
        """Run only the document-invariant audit; every finding gates."""
        ...

    @abstractmethod
    def check_skill(self) -> CheckExitCode:
        """Run only the skill-pack audit; every finding gates."""
        ...

    @abstractmethod
    def summary(self, findings: DocFindings) -> CheckSummary:
        """Collapse *findings* into one digest line."""
        ...


__all__ = ['CheckExitCode', 'CheckOnly', 'CheckSummary', 'DocFinding', 'DocFindings', 'ICheckAggregate']

#
# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "CheckExitCode": CheckExitCode,
    "CheckOnly": CheckOnly,
    "CheckSummary": CheckSummary,
    "DocFinding": DocFinding,
    "DocFindings": DocFindings,
    "ICheckAggregate": ICheckAggregate,
}
