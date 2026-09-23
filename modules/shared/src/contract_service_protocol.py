"""Service-domain protocol contract (one feature per capability ABC).

The unified service manager implements every feature ABC; injectors may type
a full manager as the composite ``IServiceManager``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_service_vo import ExitCode, ServiceTarget


class IServiceStatusProtocol(ABC):
    """FR: show status of all managed daemons."""

    @abstractmethod
    def status(self) -> ExitCode:
        """Show status of all managed daemons; return exit code."""
        ...


class IServiceStartProtocol(ABC):
    """FR: start the target daemon(s)."""

    @abstractmethod
    def start(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        """Start the target daemon(s); return exit code."""
        ...


class IServiceStopProtocol(ABC):
    """FR: stop the target daemon(s)."""

    @abstractmethod
    def stop(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        """Stop the target daemon(s); return exit code."""
        ...


class IServiceRestartProtocol(ABC):
    """FR: restart the target daemon(s)."""

    @abstractmethod
    def restart(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        """Restart the target daemon(s); return exit code."""
        ...


class IServiceLogsProtocol(ABC):
    """FR: tail logs of the target daemon."""

    @abstractmethod
    def logs(self, target: ServiceTarget = ServiceTarget("omniroute")) -> ExitCode:
        """Tail logs of the target daemon; return exit code."""
        ...


class IServiceHelpProtocol(ABC):
    """FR: print service CLI usage."""

    @abstractmethod
    def help(self) -> ExitCode:
        """Print usage; return exit code."""
        ...


class IServiceManager(
    IServiceStatusProtocol,
    IServiceStartProtocol,
    IServiceStopProtocol,
    IServiceRestartProtocol,
    IServiceLogsProtocol,
    IServiceHelpProtocol,
):
    """Composite DI type: full service-manager surface (no methods of its own)."""


__all__ = [
    "ExitCode",
    "IServiceHelpProtocol",
    "IServiceLogsProtocol",
    "IServiceManager",
    "IServiceRestartProtocol",
    "IServiceStartProtocol",
    "IServiceStatusProtocol",
    "IServiceStopProtocol",
    "ServiceTarget",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IServiceHelpProtocol": IServiceHelpProtocol,
    "IServiceLogsProtocol": IServiceLogsProtocol,
    "IServiceManager": IServiceManager,
    "IServiceRestartProtocol": IServiceRestartProtocol,
    "IServiceStartProtocol": IServiceStartProtocol,
    "IServiceStatusProtocol": IServiceStatusProtocol,
    "IServiceStopProtocol": IServiceStopProtocol,
    "ServiceTarget": ServiceTarget,
}
