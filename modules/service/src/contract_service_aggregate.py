"""Service-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations
from modules.shared.src.taxonomy_core_vo import Timestamp



from abc import ABC, abstractmethod


class IServiceAggregate(ABC):
    """Aggregate over all service-management verbs."""

    @abstractmethod
    def status(self) -> int:
        """Status of all services."""
        return None

    @abstractmethod
    def start(self, target: str = "all") -> int:
        """Start the named service(s)."""
        return None

    @abstractmethod
    def stop(self, target: str = "all") -> int:
        """Stop the named service(s)."""
        return None

    @abstractmethod
    def restart(self, target: str = "all") -> int:
        """Restart the named service(s)."""
        return None

    @abstractmethod
    def logs(self, target: str = "9router") -> int:
        """Tail service logs."""
        return None

    @abstractmethod
    def help(self) -> int:
        """Print usage."""
        return None

__all__ = ['Timestamp']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"Timestamp": Timestamp}
