"""Backup-domain protocol contract (capability ABC)."""
from __future__ import annotations
from modules.backup.src.taxonomy_backup_vo import BackupResult


from abc import ABC, abstractmethod
from pathlib import Path


class IBackupGateway(ABC):
    """Capability contract for a backup/restore transport (tar, gdrive...)."""

    @abstractmethod
    def backup(self, tool: str, dest: str = "") -> int:
        """Back up *tool*'s data dir (optionally to *dest*); return exit code."""
        return None

    @abstractmethod
    def restore(self, tool: str, archive: Path) -> int:
        """Restore *tool*'s data dir from *archive*; return exit code."""
        return None

__all__ = ['BackupResult']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"BackupResult": BackupResult}
