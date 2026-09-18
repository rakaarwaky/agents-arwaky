"""Daemon-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.daemon.contract.taxonomy_daemon_vo import DaemonStatus


class IDaemonAggregate(ABC):
    """Aggregate routing daemon verbs by daemon name."""

    @abstractmethod
    def start_daemon(self, name: str) -> int:
        """Start the named daemon."""
        raise NotImplementedError

    @abstractmethod
    def stop_daemon(self, name: str) -> int:
        """Stop the named daemon."""
        raise NotImplementedError

    @abstractmethod
    def status_daemon(self, name: str) -> DaemonStatus:
        """Status snapshot for the named daemon."""
        raise NotImplementedError

    @abstractmethod
    def logs_daemon(self, name: str) -> int:
        """Tail logs of the named daemon."""
        raise NotImplementedError

    @abstractmethod
    def restart_daemon(self, name: str) -> int:
        """Restart the named daemon."""
        raise NotImplementedError
