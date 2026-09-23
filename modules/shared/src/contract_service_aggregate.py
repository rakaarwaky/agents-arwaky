"""Service-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_service_vo import (
    TARGET_ALL,
    TARGET_OMNIROUTE,
    ExitCode,
    ServiceTarget,
)


class IServiceAggregate(ABC):
    """Aggregate over all service-management actions."""

    @abstractmethod
    def status(self) -> ExitCode:
        """Status of all services."""
        ...
    @abstractmethod
    def start(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Start the named service(s)."""
        ...
    @abstractmethod
    def stop(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Stop the named service(s)."""
        ...
    @abstractmethod
    def restart(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Restart the named service(s)."""
        ...
    @abstractmethod
    def logs(self, target: ServiceTarget = TARGET_OMNIROUTE) -> ExitCode:
        """Tail service logs."""
        ...
    @abstractmethod
    def help(self) -> ExitCode:
        """Print usage."""
        ...

__all__ = ['ExitCode', 'IServiceAggregate', 'ServiceTarget']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IServiceAggregate": IServiceAggregate, "ServiceTarget": ServiceTarget}
