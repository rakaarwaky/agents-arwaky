"""Check-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations
from modules.shared.src.taxonomy_doc_vo import DocFinding


from abc import ABC, abstractmethod


class ICheckAggregate(ABC):
    """Aggregate over all repository-verification checks."""

    @abstractmethod
    def check(self, strict: bool = False) -> int:
        """Run every check in sequence; return exit code (1 if any errors)."""
        return None

__all__ = ['DocFinding']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"DocFinding": DocFinding}
