"""Daemon-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import DaemonStatus, ExitCode


class IDaemonManager(ABC):
    """Capability contract for managing a single containerized daemon."""

    @abstractmethod
    def start(self) -> ExitCode:
        """Start the daemon (container or systemd service); return exit code."""
        return None

    @abstractmethod
    def stop(self) -> ExitCode:
        """Stop the daemon; return exit code."""
        return None

    @abstractmethod
    def status(self) -> DaemonStatus:
        """Collect a status snapshot for the daemon."""
        return None

    @abstractmethod
    def logs(self) -> ExitCode:
        """Stream/tail the daemon logs; return exit code."""
        return None

    @abstractmethod
    def restart(self) -> ExitCode:
        """Restart the daemon; return exit code."""
        return None

__all__ = ['DaemonStatus', 'ExitCode', 'IDaemonManager']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"DaemonStatus": DaemonStatus, "ExitCode": ExitCode, "IDaemonManager": IDaemonManager}
