"""Check-domain protocol contract (capability ABC)."""
from __future__ import annotations
from modules.shared.src.taxonomy_doc_vo import DocFinding


from abc import ABC, abstractmethod


class ICheckRunner(ABC):
    """Capability contract for one repository-verification check."""

    @abstractmethod
    def run(self, strict: bool = False) -> int:
        """Run the check; return the number of errors found."""
        return None

__all__ = ['DocFinding']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"DocFinding": DocFinding}
