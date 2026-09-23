"""Backup-domain protocol contract (one feature per capability ABC).

Gateways (tar, gdrive) implement every feature ABC; injectors may type a full
gateway as the composite ``IBackupGateway`` (composition only — no methods of
its own).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_backup_vo import (
    BackupDestination,
    BackupResult,
    BackupToolQuery,
    RestoreResult,
)


class IBackupProtocol(ABC):
    """FR: back up one tool's data dir via this gateway."""

    @abstractmethod
    def backup(self, tool: BackupToolQuery, dest: BackupDestination = BackupDestination("")) -> BackupResult:
        """Back up *tool*'s data dir (optionally to *dest*); return the result VO."""
        ...


class IRestoreProtocol(ABC):
    """FR: restore one tool's data dir from an archive via this gateway."""

    @abstractmethod
    def restore(self, tool: BackupToolQuery, archive: Path) -> RestoreResult:
        """Restore *tool*'s data dir from *archive*; return the result VO."""
        ...


class IListArchivesProtocol(ABC):
    """FR: list local backup archives available on this gateway."""

    @abstractmethod
    def list_archives(self) -> list[Path]:
        """List available local backup archives for this gateway."""
        ...


class IBackupGateway(
    IBackupProtocol,
    IRestoreProtocol,
    IListArchivesProtocol,
):
    """Composite DI type: full backup-gateway surface (no methods of its own)."""


__all__ = [
    "BackupResult",
    "IBackupGateway",
    "IBackupProtocol",
    "IListArchivesProtocol",
    "IRestoreProtocol",
]


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "BackupResult": BackupResult,
    "IBackupGateway": IBackupGateway,
    "IBackupProtocol": IBackupProtocol,
    "IListArchivesProtocol": IListArchivesProtocol,
    "IRestoreProtocol": IRestoreProtocol,
}
