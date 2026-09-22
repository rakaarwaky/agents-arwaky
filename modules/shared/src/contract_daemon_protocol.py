"""Daemon-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import DaemonStatus


class IDaemonManager(ABC):
    """Capability contract for managing a single containerized daemon."""

    @abstractmethod
    def start(self) -> int:
        """Start the daemon (container or systemd service); return exit code."""
        return None

    @abstractmethod
    def stop(self) -> int:
        """Stop the daemon; return exit code."""
        return None

    @abstractmethod
    def status(self) -> DaemonStatus:
        """Collect a status snapshot for the daemon."""
        return None

    @abstractmethod
    def logs(self) -> int:
        """Stream/tail the daemon logs; return exit code."""
        return None

    @abstractmethod
    def restart(self) -> int:
        """Restart the daemon; return exit code."""
        return None
