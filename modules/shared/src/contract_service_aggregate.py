"""Service-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_service_vo import ExitCode, ServiceTarget


class IServiceAggregate(ABC):
    """Aggregate over all service-management verbs."""

    @abstractmethod
    def status(self) -> ExitCode:
        """Status of all services."""
        return None

    @abstractmethod
    def start(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        """Start the named service(s)."""
        return None

    @abstractmethod
    def stop(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        """Stop the named service(s)."""
        return None

    @abstractmethod
    def restart(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        """Restart the named service(s)."""
        return None

    @abstractmethod
    def logs(self, target: ServiceTarget = ServiceTarget("omniroute")) -> ExitCode:
        """Tail service logs."""
        return None

    @abstractmethod
    def help(self) -> ExitCode:
        """Print usage."""
        return None

__all__ = ['ExitCode', 'IServiceAggregate', 'ServiceTarget']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IServiceAggregate": IServiceAggregate, "ServiceTarget": ServiceTarget}
