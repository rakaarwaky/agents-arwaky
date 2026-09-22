from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_service_vo import ExitCode, ServiceTarget


class IServiceManager(ABC):
    """Capability contract for the unified service manager."""

    @abstractmethod
    def status(self) -> ExitCode:
        """Show status of all managed daemons; return exit code."""
        return None

    @abstractmethod
    def start(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        """Start the target daemon(s); return exit code."""
        return None

    @abstractmethod
    def stop(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        """Stop the target daemon(s); return exit code."""
        return None

    @abstractmethod
    def restart(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        """Restart the target daemon(s); return exit code."""
        return None

    @abstractmethod
    def logs(self, target: ServiceTarget = ServiceTarget("omniroute")) -> ExitCode:
        """Tail logs of the target daemon; return exit code."""
        return None

    @abstractmethod
    def help(self) -> ExitCode:
        """Print usage."""
        return None

__all__ = ['ExitCode', 'IServiceManager', 'ServiceTarget']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IServiceManager": IServiceManager, "ServiceTarget": ServiceTarget}
