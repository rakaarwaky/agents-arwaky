"""Backup-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IBackupGateway(ABC):
    """Capability contract for a backup/restore transport (tar, gdrive...)."""

    @abstractmethod
    def backup(self, tool: str, dest: str = "") -> int:
        """Back up *tool*'s data dir (optionally to *dest*); return exit code."""
        raise NotImplementedError

    @abstractmethod
    def restore(self, tool: str, archive: Path) -> int:
        """Restore *tool*'s data dir from *archive*; return exit code."""
        raise NotImplementedError
