"""Daemon-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.daemon.src.taxonomy_daemon_vo import DaemonStatus


class IDaemonAggregate(ABC):
    """Aggregate routing daemon verbs by daemon name."""

    @abstractmethod
    def start_daemon(self, name: str) -> int:
        """Start the named daemon."""
        return None

    @abstractmethod
    def stop_daemon(self, name: str) -> int:
        """Stop the named daemon."""
        return None

    @abstractmethod
    def status_daemon(self, name: str) -> DaemonStatus:
        """Status snapshot for the named daemon."""
        return None

    @abstractmethod
    def logs_daemon(self, name: str) -> int:
        """Tail logs of the named daemon."""
        return None

    @abstractmethod
    def restart_daemon(self, name: str) -> int:
        """Restart the named daemon."""
        return None
