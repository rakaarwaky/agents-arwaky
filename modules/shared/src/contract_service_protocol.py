from modules.shared.src.taxonomy_core_vo import Timestamp

from abc import ABC, abstractmethod


class IServiceManager(ABC):
    """Capability contract for the unified service manager."""

    @abstractmethod
    def status(self) -> int:
        """Show status of all managed daemons; return exit code."""
        return None

    @abstractmethod
    def start(self, target: str = "all") -> int:
        """Start the target daemon(s); return exit code."""
        return None

    @abstractmethod
    def stop(self, target: str = "all") -> int:
        """Stop the target daemon(s); return exit code."""
        return None

    @abstractmethod
    def restart(self, target: str = "all") -> int:
        """Restart the target daemon(s); return exit code."""
        return None

    @abstractmethod
    def logs(self, target: str = "omniroute") -> int:
        """Tail logs of the target daemon; return exit code."""
        return None

__all__ = ['Timestamp']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"Timestamp": Timestamp}
