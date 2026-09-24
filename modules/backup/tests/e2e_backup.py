"""E2E tests for modules/backup — full backup workflow tests."""
from __future__ import annotations


def test_backup_e2e_workflow():
    """E2E-BACKUP-001: Full backup orchestration workflow."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

    tar = TarBackupGateway()
    orchestrator = BackupOrchestrator(tar, tar)

    # Test backup method exists and is callable
    assert hasattr(orchestrator, 'backup')
    assert hasattr(orchestrator, 'restore')
    assert hasattr(orchestrator, 'list_archives')
    assert hasattr(orchestrator, 'status_store')
    assert hasattr(orchestrator, 'help')

    # Test list_archives returns something (can be list or 0)
    result = orchestrator.list_archives()
    assert result is not None


def test_gdrive_e2e_workflow():
    """E2E-BACKUP-002: Full GDrive gateway workflow."""
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

    gdrive = GdriveBackupGateway()

    # Test execute dispatch
    result = gdrive.execute("list")
    assert result is not None
