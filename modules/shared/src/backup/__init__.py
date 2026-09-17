"""Shared backup-domain: taxonomy + contracts for backup/restore."""
from modules.shared.src.backup.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.backup.contract_backup_protocol import IBackupGateway
from modules.shared.src.backup.taxonomy_backup_vo import BackupResult, RestoreResult

__all__ = [
    "IBackupAggregate",
    "IBackupGateway",
    "BackupResult",
    "RestoreResult",
]
