"""Backup composition root — wires the tar + gdrive gateways into the orchestrator."""
from __future__ import annotations

from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway
from modules.backup.src.capabilities_backup_tar import TarBackupGateway
from modules.shared.src.contract_backup_aggregate import IBackupAggregate


class BackupContainer:
    """Construct the two backup gateways and the orchestrator."""

    def __init__(self) -> None:
        tar_gateway = TarBackupGateway()
        gdrive_gateway = GdriveBackupGateway()
        self._orchestrator = BackupOrchestrator(tar_gateway, gdrive_gateway)

    @property
    def aggregate(self) -> IBackupAggregate:
        return self._orchestrator


def create_backup_feature() -> IBackupAggregate:
    """Fully-wired backup feature aggregate."""
    return BackupContainer().aggregate
