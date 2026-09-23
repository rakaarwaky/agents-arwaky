"""Backup-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_backup_vo import (
    DEST_DEFAULT,
    BackupArchive,
    BackupDestination,
    BackupResult,
    BackupToolQuery,
    ExitCode,
)


class IBackupAggregate(ABC):
    """Aggregate over backup/restore orchestration."""

    @abstractmethod
    def backup(self, tool: BackupToolQuery, dest: BackupDestination = DEST_DEFAULT) -> ExitCode:
        """Back up *tool* (or all tools); return exit code."""
        ...
    @abstractmethod
    def restore(self, tool: BackupToolQuery, archive: BackupArchive) -> ExitCode:
        """Restore *tool* from *archive*; return exit code."""
        ...
    @abstractmethod
    def list_archives(self) -> ExitCode:
        """List available local backup archives; return exit code."""
        ...
    @abstractmethod
    def status_store(self) -> ExitCode:
        """Report backup store path / existence / archive count; return exit code."""
        ...
    @abstractmethod
    def help(self) -> ExitCode:
        """Print backup/restore usage; return exit code."""
        ...

__all__ = ["BackupResult", "IBackupAggregate"]


#: Per-tool backup result cache (populated by orchestrators; layer wiring).
_BACKUP_RESULT_CACHE: dict[str, BackupResult] = {}

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"BackupResult": BackupResult}
