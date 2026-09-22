"""Backup-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_backup_vo import (
    BackupDestination,
    BackupResult,
    BackupToolQuery,
    RestoreResult,
)


class IBackupGateway(ABC):
    """Capability contract for a backup/restore transport (tar, gdrive...)."""

    @abstractmethod
    def backup(self, tool: BackupToolQuery, dest: BackupDestination = BackupDestination("")) -> BackupResult:
        """Back up *tool*'s data dir (optionally to *dest*); return the result VO."""
        return None

    @abstractmethod
    def restore(self, tool: BackupToolQuery, archive: Path) -> RestoreResult:
        """Restore *tool*'s data dir from *archive*; return the result VO."""
        return None

    @abstractmethod
    def list_archives(self) -> list[Path]:
        """List available local backup archives for this gateway."""
        return []

__all__ = ['BackupResult']


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"BackupResult": BackupResult}
