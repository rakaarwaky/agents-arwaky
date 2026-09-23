"""Backup-domain protocol contract (one feature, one capability ABC).

A single ``execute`` method dispatches every backup capability — archive,
restore, list, list_print, status, help — by operation; injectors may type
any gateway or adapter that can run an operation as ``IBackupProtocol``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_backup_vo import (
    ARCHIVE_DEFAULT,
    DEST_DEFAULT,
    BackupArchive,
    BackupDestination,
    BackupOp,
    BackupResult,
    BackupToolQuery,
    ExitCode,
)


class IBackupProtocol(ABC):
    """FR: run one backup operation through this gateway/adapter."""

    @abstractmethod
    def execute(
        self,
        op: BackupOp,
        tool: BackupToolQuery | None = None,
        dest: BackupDestination = DEST_DEFAULT,
        archive: BackupArchive = ARCHIVE_DEFAULT,
    ) -> BackupResult | ExitCode:
        """Dispatch *op* (archive | restore | list | list_print | status | help) with the optional
        *tool* / *dest* / *archive* arguments; return the operation result
        (result object, archive list, or int status/help exit code).
        """
        ...


__all__ = [
    "ARCHIVE_DEFAULT",
    "DEST_DEFAULT",
    "BackupArchive",
    "BackupDestination",
    "BackupOp",
    "BackupResult",
    "BackupToolQuery",
    "ExitCode",
    "IBackupProtocol",
]


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ARCHIVE_DEFAULT": ARCHIVE_DEFAULT,
    "DEST_DEFAULT": DEST_DEFAULT,
    "BackupArchive": BackupArchive,
    "BackupDestination": BackupDestination,
    "BackupOp": BackupOp,
    "BackupResult": BackupResult,
    "BackupToolQuery": BackupToolQuery,
    "ExitCode": ExitCode,
    "IBackupProtocol": IBackupProtocol,
}
