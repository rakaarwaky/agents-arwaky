"""Check-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_check_vo import CheckExitCode
from modules.shared.src.taxonomy_common_vo import DocFinding


class ICheckProtocol(ABC):
    """Capability contract for one repository-verification check."""

    #: Stable CLI key for selective runs — ``docs`` | ``skill``.
    name: str = ""

    @abstractmethod
    def run(self) -> CheckExitCode:
        """Run the check strictly (every finding gates); return the error count."""
        ...

__all__ = ['CheckExitCode', 'DocFinding']

#
# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"CheckExitCode": CheckExitCode, "DocFinding": DocFinding}
