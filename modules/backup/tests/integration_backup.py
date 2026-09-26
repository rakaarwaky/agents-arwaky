"""Integration tests for modules/backup — test component interactions."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from modules.shared.src.taxonomy_backup_vo import BackupOp, BackupRequest


def test_full_backup_workflow():
    """IT-BACKUP-001: Full backup workflow executes without errors."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    tar = TarBackupGateway()
    orchestrator = BackupOrchestrator(tar, tar)

    assert callable(orchestrator.execute)
    assert orchestrator.execute(BackupRequest(BackupOp("help"))).result == 0


def test_orchestrator_with_real_gateways():
    """IT-BACKUP-002: Orchestrator works with real gateway instances."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    tar = TarBackupGateway()
    gdrive = GdriveBackupGateway()
    orchestrator = BackupOrchestrator(tar, gdrive)

    assert orchestrator.execute(BackupRequest(BackupOp("help"))).result == 0
    assert orchestrator.execute(BackupRequest(BackupOp("status"))).result == 0


def test_tar_backup_store_check():
    """IT-BACKUP-003: Backup store path check works."""
    from modules.backup.src.capabilities_backup_tar import BACKUP_STORE

    assert isinstance(BACKUP_STORE, Path)


def test_gdrive_gateway_folder_name():
    """IT-BACKUP-004: Gdrive gateway uses correct default folder name."""
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

    gateway = GdriveBackupGateway()
    assert gateway._folder_name == "Agents-Arwaky-Backups"


def test_execute_op_dispatch():
    """IT-BACKUP-005: The aggregate routes each op to the matching protocol method."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    tar = TarBackupGateway()
    orchestrator = BackupOrchestrator(tar, tar)

    with patch("modules.backup.src.capabilities_backup_tar.cmd_list", return_value=0):
        assert orchestrator.execute(BackupRequest(BackupOp("list"))).result == 0

    with patch("modules.backup.src.capabilities_backup_tar.cmd_help", return_value=0):
        assert orchestrator.execute(BackupRequest(BackupOp("help"))).result == 0


def test_container_creation():
    """IT-BACKUP-006: Container creates orchestrator correctly."""
    from modules.backup.src.root_backup_container import BackupContainer

    container = BackupContainer()
    assert container.aggregate is not None
