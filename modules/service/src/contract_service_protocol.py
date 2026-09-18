
from abc import ABC, abstractmethod


class IServiceManager(ABC):
    """Capability contract for the unified service manager."""

    @abstractmethod
    def status(self) -> int:
        """Show status of all managed daemons; return exit code."""
        raise NotImplementedError

    @abstractmethod
    def start(self, target: str = "all") -> int:
        """Start the target daemon(s); return exit code."""
        raise NotImplementedError

    @abstractmethod
    def stop(self, target: str = "all") -> int:
        """Stop the target daemon(s); return exit code."""
        raise NotImplementedError

    @abstractmethod
    def restart(self, target: str = "all") -> int:
        """Restart the target daemon(s); return exit code."""
        raise NotImplementedError

    @abstractmethod
    def logs(self, target: str = "9router") -> int:
        """Tail logs of the target daemon; return exit code."""
        raise NotImplementedError
