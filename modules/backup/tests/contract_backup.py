"""Contract tests for modules/backup — verify protocol implementations."""
from __future__ import annotations

from pathlib import Path


def test_backup_protocol_exists():
    """CP-BACKUP-001: IBackupProtocol exists and can be imported."""
    from modules.shared.src.contract_backup_protocol import IBackupProtocol

    assert IBackupProtocol is not None


def test_backup_vo_classes_exist():
    """CP-BACKUP-002: Backup VO classes are defined."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

    assert TarBackupGateway is not None
    assert GdriveBackupGateway is not None
    assert BackupOrchestrator is not None


def test_tartape_gateway_implements_protocol():
    """CP-BACKUP-003: TarBackupGateway implements IBackupProtocol."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.shared.src.contract_backup_protocol import IBackupProtocol

    gateway = TarBackupGateway()
    assert isinstance(gateway, IBackupProtocol)


def test_gdrive_gateway_implements_protocol():
    """CP-BACKUP-004: GdriveBackupGateway implements IBackupProtocol."""
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway
    from modules.shared.src.contract_backup_protocol import IBackupProtocol

    gateway = GdriveBackupGateway()
    assert isinstance(gateway, IBackupProtocol)


def test_backup_orchestrator_exists():
    """CP-BACKUP-005: BackupOrchestrator class exists."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

    assert BackupOrchestrator is not None


def test_backup_constants_defined():
    """CP-BACKUP-006: Backup module constants are defined."""
    from modules.backup.src.capabilities_backup_tar import BACKUP_STORE, GDRIVE_HELPER
    from modules.backup.src.capabilities_backup_gdrive import DEFAULT_FOLDER_NAME

    assert BACKUP_STORE is not None
    assert isinstance(BACKUP_STORE, Path)
    assert isinstance(GDRIVE_HELPER, str)
    assert isinstance(DEFAULT_FOLDER_NAME, str)
    assert DEFAULT_FOLDER_NAME == "Agents-Arwaky-Backups"


def test_backup_execute_method_exists():
    """CP-BACKUP-007: Gateway classes have execute method."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

    tar = TarBackupGateway()
    gdrive = GdriveBackupGateway()

    assert hasattr(tar, 'execute')
    assert hasattr(gdrive, 'execute')
    assert callable(getattr(tar, 'execute'))
    assert callable(getattr(gdrive, 'execute'))


def test_backup_orchestrator_methods():
    """CP-BACKUP-008: BackupOrchestrator has required methods."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    orchestrator = BackupOrchestrator(TarBackupGateway(), TarBackupGateway())

    assert hasattr(orchestrator, 'backup')
    assert hasattr(orchestrator, 'restore')
    assert hasattr(orchestrator, 'list_archives')
    assert hasattr(orchestrator, 'status_store')
    assert hasattr(orchestrator, 'help')
