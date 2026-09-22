"""Backup-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations
from modules.backup.src.taxonomy_backup_vo import BackupResult


from abc import ABC, abstractmethod


class IBackupAggregate(ABC):
    """Aggregate over backup/restore orchestration."""

    @abstractmethod
    def backup(self, tool: str, dest: str = "") -> int:
        """Back up *tool* (or all tools); return exit code."""
        return None

    @abstractmethod
    def restore(self, tool: str, archive: str) -> int:
        """Restore *tool* from *archive*; return exit code."""
        return None

    @abstractmethod
    def list_archives(self) -> int:
        """List available local backup archives; return exit code."""
        return None

__all__ = ['BackupResult'
    'BackupResult',
]


#: Per-tool backup result cache (populated by orchestrators; layer wiring).
_BACKUP_RESULT_CACHE: "dict[str, BackupResult]" = {}

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"BackupResult": BackupResult}
