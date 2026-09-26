"""Backup-domain aggregate contract (agent orchestrator ABC).

Single entry point over the backup feature: the surface, root, CLI and MCP
call ``execute`` with a request and get a response back. The agent behind
the aggregate routes each ``op`` to the matching protocol method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_backup_vo import (
    BackupOutcome,
    BackupRequest,
    BackupResponse,
)


class IBackupAggregate(ABC):
    """Single entry point over backup/restore orchestration."""

    @abstractmethod
    def execute(self, request: BackupRequest) -> BackupResponse:
        """Run the request the surface/root/CLI/MCP asked for; return the response."""
        ...


__all__ = ["BackupOutcome", "BackupRequest", "BackupResponse", "IBackupAggregate"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "BackupOutcome": BackupOutcome,
    "BackupRequest": BackupRequest,
    "BackupResponse": BackupResponse,
    "IBackupAggregate": IBackupAggregate,
}
