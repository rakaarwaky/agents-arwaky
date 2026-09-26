"""E2E tests for modules/backup — full backup workflow tests."""
from __future__ import annotations

from unittest.mock import patch

from modules.shared.src.taxonomy_backup_vo import BackupOp, BackupRequest


def test_backup_e2e_workflow():
    """E2E-BACKUP-001: Full backup orchestration workflow."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    tar = TarBackupGateway()
    orchestrator = BackupOrchestrator(tar, tar)

    # The aggregate is a single entry point.
    assert callable(orchestrator.execute)

    with patch("modules.backup.src.capabilities_backup_tar.cmd_list", return_value=0):
        result = orchestrator.execute(BackupRequest(BackupOp("list")))
    assert result.result == 0


def test_gdrive_e2e_workflow():
    """E2E-BACKUP-002: Full GDrive gateway workflow."""
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

    gdrive = GdriveBackupGateway()

    # The gateway exposes rich named methods, not an execute(op) bag.
    for method in ("backup", "restore", "list_archives", "status", "help"):
        assert callable(getattr(gdrive, method))
