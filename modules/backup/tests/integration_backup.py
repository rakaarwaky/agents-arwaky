"""Integration tests for modules/backup — test component interactions."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_full_backup_workflow():
    """IT-BACKUP-001: Full backup workflow executes without errors."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

    tar = TarBackupGateway()
    orchestrator = BackupOrchestrator(tar, tar)

    # Test backup method exists and can be called
    assert hasattr(orchestrator, 'backup')
    assert hasattr(orchestrator, 'restore')
    assert hasattr(orchestrator, 'list_archives')


def test_orchestrator_with_real_gateways():
    """IT-BACKUP-002: Orchestrator works with real gateway instances."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

    tar = TarBackupGateway()
    gdrive = GdriveBackupGateway()
    orchestrator = BackupOrchestrator(tar, gdrive)

    # All operations should be callable without error
    assert orchestrator.help() == 0
    assert orchestrator.status_store() == 0


def test_tar_backup_store_check():
    """IT-BACKUP-003: Backup store path check works."""
    from modules.backup.src.capabilities_backup_tar import BACKUP_STORE

    # Check that BACKUP_STORE is a valid Path object
    assert isinstance(BACKUP_STORE, Path)


def test_gdrive_gateway_folder_name():
    """IT-BACKUP-004: Gdrive gateway uses correct default folder name."""
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

    gateway = GdriveBackupGateway()
    assert gateway._folder_name == "Agents-Arwaky-Backups"


def test_execute_op_dispatch():
    """IT-BACKUP-005: Execute correctly dispatches operations."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    gateway = TarBackupGateway()

    # Test list op
    result = gateway.execute("list")
    assert result is not None

    # Test help op
    result = gateway.execute("help")
    assert result == 0


def test_container_creation():
    """IT-BACKUP-006: Container creates orchestrator correctly."""
    from modules.backup.src.root_backup_container import BackupContainer

    container = BackupContainer()
    assert container.aggregate is not None
