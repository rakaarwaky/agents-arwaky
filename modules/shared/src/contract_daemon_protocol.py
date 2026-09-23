"""Daemon-domain protocol contract (one feature per capability ABC).

Daemon managers (podman, anytype container) implement every feature ABC;
injectors may type a full manager as the composite ``IDaemonManager``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import DaemonStatus, ExitCode


class IDaemonStartProtocol(ABC):
    """FR: start the daemon (container or systemd unit)."""

    @abstractmethod
    def start(self) -> ExitCode:
        """Start the daemon; return exit code."""
        ...


class IDaemonStopProtocol(ABC):
    """FR: stop the daemon."""

    @abstractmethod
    def stop(self) -> ExitCode:
        """Stop the daemon; return exit code."""
        ...


class IDaemonStatusProtocol(ABC):
    """FR: collect a status snapshot for the daemon."""

    @abstractmethod
    def status(self) -> DaemonStatus:
        """Collect a status snapshot for the daemon."""
        ...


class IDaemonLogsProtocol(ABC):
    """FR: stream/tail the daemon logs."""

    @abstractmethod
    def logs(self) -> ExitCode:
        """Stream/tail the daemon logs; return exit code."""
        ...


class IDaemonRestartProtocol(ABC):
    """FR: restart the daemon."""

    @abstractmethod
    def restart(self) -> ExitCode:
        """Restart the daemon; return exit code."""
        ...


class IDaemonManager(
    IDaemonStartProtocol,
    IDaemonStopProtocol,
    IDaemonStatusProtocol,
    IDaemonLogsProtocol,
    IDaemonRestartProtocol,
):
    """Composite DI type: full daemon-manager surface (no methods of its own)."""


__all__ = [
    "DaemonStatus",
    "ExitCode",
    "IDaemonLogsProtocol",
    "IDaemonManager",
    "IDaemonRestartProtocol",
    "IDaemonStartProtocol",
    "IDaemonStatusProtocol",
    "IDaemonStopProtocol",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonStatus": DaemonStatus,
    "ExitCode": ExitCode,
    "IDaemonLogsProtocol": IDaemonLogsProtocol,
    "IDaemonManager": IDaemonManager,
    "IDaemonRestartProtocol": IDaemonRestartProtocol,
    "IDaemonStartProtocol": IDaemonStartProtocol,
    "IDaemonStatusProtocol": IDaemonStatusProtocol,
    "IDaemonStopProtocol": IDaemonStopProtocol,
}
