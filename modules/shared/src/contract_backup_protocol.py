"""Backup-domain protocol contract (one feature, one capability ABC).

A single ``execute`` method dispatches every backup capability — archive,
restore, list — by operation (status/help stay on the aggregate); injectors
may type any gateway or adapter that can run an operation as
``IBackupProtocol``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_backup_vo import (
    DEST_DEFAULT,
    BackupDestination,
    BackupResult,
    BackupToolQuery,
)


class IBackupProtocol(ABC):
    """FR: run one backup operation through this gateway/adapter."""

    @abstractmethod
    def execute(
        self,
        op: str,
        tool: BackupToolQuery | None = None,
        dest: BackupDestination = DEST_DEFAULT,
        archive: str = "",
    ) -> object:
        """Dispatch *op* (archive / restore / list) with the optional
        *tool* / *dest* / *archive* arguments; return the operation result
        (result object or archive / list path).
        """
        ...


__all__ = ["BackupResult", "IBackupProtocol"]


# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "BackupResult": BackupResult,
    "IBackupProtocol": IBackupProtocol,
}
