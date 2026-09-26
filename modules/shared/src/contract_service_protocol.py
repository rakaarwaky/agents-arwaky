"""Service-domain protocol contract (capability ABC).

Pure capability ABC: one abstract method per service operation the unified
manager exposes. Consumers never see this method list — the aggregate
dispatches to it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_service_vo import (
    TARGET_9ROUTER,
    TARGET_ALL,
    ExitCode,
    ServiceTarget,
)


class IServiceProtocol(ABC):
    """Capability contract for the unified service manager: one method per op."""

    @abstractmethod
    def status(self) -> ExitCode:
        """Report the health of every registered service. Return the exit code."""
        ...

    @abstractmethod
    def start(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Start the named service(s). Return the exit code."""
        ...

    @abstractmethod
    def stop(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Stop the named service(s). Return the exit code."""
        ...

    @abstractmethod
    def restart(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Restart the named service(s). Return the exit code."""
        ...

    @abstractmethod
    def logs(self, target: ServiceTarget = TARGET_9ROUTER) -> ExitCode:
        """Stream the named service's logs. Return the exit code."""
        ...

    @abstractmethod
    def help(self) -> ExitCode:
        """Print the service command usage. Return the exit code."""
        ...


__all__ = [
    "TARGET_9ROUTER",
    "TARGET_ALL",
    "ExitCode",
    "IServiceProtocol",
    "ServiceTarget",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "TARGET_9ROUTER": TARGET_9ROUTER,
    "TARGET_ALL": TARGET_ALL,
    "ExitCode": ExitCode,
    "IServiceProtocol": IServiceProtocol,
    "ServiceTarget": ServiceTarget,
}
