"""Backup-domain protocol contract (capability ABC).

Capability ABCs for the backup subsystems. The feature splits its seams
across two protocols so the aggregate coordinates two distinct subsystems:

- ``IBackupControlProtocol`` — mutation ops: archive and restore.
- ``IBackupInspectProtocol`` — read-only store ops: list, status, help.

Each method carries its own typed return, so a gateway implementor never
narrows a union and never dispatches behind an ``execute(op, …)`` bag.
Consumers never see this method list; the aggregate dispatches to it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.backup.taxonomy_backup_vo import (
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


class IBackupControlProtocol(ABC):
    """Capability contract for backup mutation: archive and restore."""

    @abstractmethod
    def backup(self, tool: BackupToolQuery, dest: BackupDestination = DEST_DEFAULT) -> BackupResult:
        """Archive *tool*'s XDG state into *dest*; return the backup result."""
        ...

    @abstractmethod
    def restore(self, tool: BackupToolQuery, archive: BackupArchive = ARCHIVE_DEFAULT) -> RestoreResult:
        """Restore *tool*'s XDG state from *archive*; return the restore result."""
        ...


class IBackupInspectProtocol(ABC):
    """Capability contract for read-only store ops: list, status, help."""

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
    "DEST_DEFAULT",
    "BackupArchive",
    "BackupDestination",
    "BackupOutcome",
    "BackupResult",
    "BackupToolQuery",
    "ExitCode",
    "IBackupControlProtocol",
    "IBackupInspectProtocol",
    "RestoreResult",
]


