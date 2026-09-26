"""Backup-domain protocol contract (capability ABC).

Pure capability ABC: one abstract method per backup operation a gateway
exposes — archive, restore, list, status, help. Each method carries its
own typed return, so a gateway implementor never narrows a union and never
dispatches behind an ``execute(op, …)`` bag. Consumers never see this
method list; the aggregate dispatches to it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_backup_vo import (
    ARCHIVE_DEFAULT,
    DEST_DEFAULT,
    BackupArchive,
    BackupDestination,
    BackupOutcome,
    BackupResult,
    BackupToolQuery,
    ExitCode,
    RestoreResult,
)


class IBackupProtocol(ABC):
    """Capability contract for backup gateways: one method per operation."""

    @abstractmethod
    def backup(self, tool: BackupToolQuery, dest: BackupDestination = DEST_DEFAULT) -> BackupResult:
        """Archive *tool*'s XDG state into *dest*; return the backup result."""
        ...

    @abstractmethod
    def restore(self, tool: BackupToolQuery, archive: BackupArchive = ARCHIVE_DEFAULT) -> RestoreResult:
        """Restore *tool*'s XDG state from *archive*; return the restore result."""
        ...

    @abstractmethod
    def list_archives(self) -> BackupOutcome:
        """Return the archives visible to this gateway plus their print lines."""
        ...

    @abstractmethod
    def status(self) -> ExitCode:
        """Report the backup store path, existence, and archive count; return exit code."""
        ...

    @abstractmethod
    def help(self) -> ExitCode:
        """Print backup/restore usage; return exit code."""
        ...


__all__ = [
    "ARCHIVE_DEFAULT",
    "BackupArchive",
    "BackupDestination",
    "BackupOutcome",
    "BackupResult",
    "BackupToolQuery",
    "ExitCode",
    "IBackupProtocol",
    "RestoreResult",
    "DEST_DEFAULT",
]


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ARCHIVE_DEFAULT": ARCHIVE_DEFAULT,
    "BackupArchive": BackupArchive,
    "BackupDestination": BackupDestination,
    "BackupOutcome": BackupOutcome,
    "BackupResult": BackupResult,
    "BackupToolQuery": BackupToolQuery,
    "ExitCode": ExitCode,
    "IBackupProtocol": IBackupProtocol,
    "RestoreResult": RestoreResult,
    "DEST_DEFAULT": DEST_DEFAULT,
}
