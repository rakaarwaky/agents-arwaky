"""Backup-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class IBackupAggregate(ABC):
    """Aggregate over backup/restore orchestration."""

    @abstractmethod
    def backup(self, tool: str, dest: str = "") -> int:
        """Back up *tool* (or all tools); return exit code."""
        raise NotImplementedError

    @abstractmethod
    def restore(self, tool: str, archive: str) -> int:
        """Restore *tool* from *archive*; return exit code."""
        raise NotImplementedError

    @abstractmethod
    def list_archives(self) -> int:
        """List available local backup archives; return exit code."""
        raise NotImplementedError
