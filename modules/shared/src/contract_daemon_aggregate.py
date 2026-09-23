"""Daemon-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import DaemonName, DaemonStatus, ExitCode


class IDaemonAggregate(ABC):
    """Aggregate routing daemon actions by daemon name."""

    @abstractmethod
    def start_daemon(self, name: DaemonName) -> ExitCode:
        """Start the named daemon."""
        return None

    @abstractmethod
    def stop_daemon(self, name: DaemonName) -> ExitCode:
        """Stop the named daemon."""
        return None

    @abstractmethod
    def status_daemon(self, name: DaemonName) -> DaemonStatus:
        """Status snapshot for the named daemon."""
        return None

    @abstractmethod
    def logs_daemon(self, name: DaemonName) -> ExitCode:
        """Tail logs of the named daemon."""
        return None

    @abstractmethod
    def restart_daemon(self, name: DaemonName) -> ExitCode:
        """Restart the named daemon."""
        return None

__all__ = ['DaemonName', 'DaemonStatus', 'ExitCode', 'IDaemonAggregate']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonName": DaemonName,
    "DaemonStatus": DaemonStatus,
    "ExitCode": ExitCode,
    "IDaemonAggregate": IDaemonAggregate,
}
