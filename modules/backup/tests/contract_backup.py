"""Contract tests for modules/backup — verify protocol implementations."""
from __future__ import annotations


def test_backup_protocol_exists():
    """CP-BACKUP-001: IBackupProtocol exists and can be imported."""
    from modules.shared.src.backup.contract_backup_protocol import IBackupProtocol

    assert IBackupProtocol is not None

def test_backup_vo_classes_exist():
    """CP-BACKUP-002: Backup VO classes are defined."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    assert TarBackupGateway is not None
    assert BackupOrchestrator is not None

def test_tar_gateway_implements_protocol():
    """CP-BACKUP-003: TarBackupGateway implements the rich IBackupProtocol."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.shared.src.backup.contract_backup_protocol import IBackupProtocol

    gateway = TarBackupGateway()
    assert isinstance(gateway, IBackupProtocol)
    for method in ("backup", "restore", "list_archives", "status", "help"):
        assert callable(getattr(gateway, method))

def test_backup_orchestrator_exists():
    """CP-BACKUP-005: BackupOrchestrator class exists."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

    assert BackupOrchestrator is not None

def test_backup_orchestrator_dispatches_to_tar():
    """CP-BACKUP-006: BackupOrchestrator dispatches backup ops to the tar gateway."""
    from unittest.mock import MagicMock

    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
    from modules.shared.src.backup.taxonomy_backup_vo import (
        BackupArchive,
        BackupDestination,
        BackupOp,
        BackupRequest,
        BackupToolQuery,
    )

    tar = MagicMock()
    tar.backup.return_value = MagicMock(success=True, tool_id="omniroute", archive="omniroute.tar.gz", uploaded=False, message="ok")
    tar.restore.return_value = MagicMock(success=True, tool_id="omniroute", archive="omniroute.tar.gz", message="ok")
    tar.list_archives.return_value = MagicMock(success=True, tool_id="", result=[])
    tar.help.return_value = 0
    tar.status.return_value = 0

    orchestrator = BackupOrchestrator(tar)

    response = orchestrator.execute(BackupRequest(BackupOp("backup"), tool=BackupToolQuery("omniroute"), dest=BackupDestination("")))
    tar.backup.assert_called_once()
    assert response.success is True

    response = orchestrator.execute(BackupRequest(BackupOp("restore"), tool=BackupToolQuery("omniroute"), archive=BackupArchive("omniroute.tar.gz")))
    tar.restore.assert_called_once()
    assert response.success is True

    response = orchestrator.execute(BackupRequest(BackupOp("list")))
    tar.list_archives.assert_called_once()
    assert response.success is True

    response = orchestrator.execute(BackupRequest(BackupOp("help")))
    tar.help.assert_called_once()
    assert response.success is True

    response = orchestrator.execute(BackupRequest(BackupOp("status")))
    tar.status.assert_called_once()
    assert response.success is True