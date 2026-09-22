"""Backup-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_backup_vo import (
    BackupArchive,
    BackupDestination,
    BackupResult,
    BackupToolQuery,
    ExitCode,
)


class IBackupAggregate(ABC):
    """Aggregate over backup/restore orchestration."""

    @abstractmethod
    def backup(self, tool: BackupToolQuery, dest: BackupDestination = BackupDestination("")) -> ExitCode:
        """Back up *tool* (or all tools); return exit code."""
        return None

    @abstractmethod
    def restore(self, tool: BackupToolQuery, archive: BackupArchive) -> ExitCode:
        """Restore *tool* from *archive*; return exit code."""
        return None

    @abstractmethod
    def list_archives(self) -> ExitCode:
        """List available local backup archives; return exit code."""
        return None

__all__ = ["BackupResult", "IBackupAggregate"]


#: Per-tool backup result cache (populated by orchestrators; layer wiring).
_BACKUP_RESULT_CACHE: dict[str, BackupResult] = {}

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"BackupResult": BackupResult}
