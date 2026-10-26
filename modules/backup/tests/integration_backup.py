"""Integration tests for modules/backup — test component interactions."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.backup.taxonomy_backup_vo import BackupOp, BackupRequest


def test_full_backup_workflow():
    """IT-BACKUP-001: Full backup workflow executes without errors."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
    from modules.backup.src.capabilities_backup_inspect import TarBackupInspect
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    tar = TarBackupGateway()
    orchestrator = BackupOrchestrator(tar, TarBackupInspect())

    assert callable(orchestrator.execute)
    assert orchestrator.execute(BackupRequest(BackupOp("help"))).result == 0

def test_orchestrator_with_real_gateways():
    """IT-BACKUP-002: Orchestrator works with real gateway instances."""
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
    from modules.backup.src.capabilities_backup_inspect import TarBackupInspect
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway

    tar = TarBackupGateway()
    orchestrator = BackupOrchestrator(tar, TarBackupInspect())

    assert orchestrator.execute(BackupRequest(BackupOp("help"))).result == 0
    assert orchestrator.execute(BackupRequest(BackupOp("status"))).result == 0

def test_tar_backup_store_check():
    """IT-BACKUP-003: Backup store path check works."""
    from modules.backup.src.capabilities_backup_tar import BACKUP_STORE

    assert isinstance(BACKUP_STORE, Path)

def test_execute_op_dispatch():
    """IT-BACKUP-004: The aggregate routes each op to the matching protocol method."""
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
    tar.backup.return_value = MagicMock(success=True, tool_id="omniroute", archive="omniroute.tar.gz", message="ok")
    tar.restore.return_value = MagicMock(success=True, tool_id="omniroute", archive="omniroute.tar.gz", message="ok")
    inspect_cap = MagicMock()
    inspect_cap.list_archives.return_value = MagicMock(success=True, tool_id="", result=[])
    inspect_cap.help.return_value = 0
    inspect_cap.status.return_value = 0

    orchestrator = BackupOrchestrator(tar, inspect_cap)

    orchestrator.execute(BackupRequest(BackupOp("backup"), tool=BackupToolQuery("omniroute"), dest=BackupDestination("")))
    tar.backup.assert_called_once()

    orchestrator.execute(BackupRequest(BackupOp("restore"), tool=BackupToolQuery("omniroute"), archive=BackupArchive("omniroute.tar.gz")))
    tar.restore.assert_called_once()

    orchestrator.execute(BackupRequest(BackupOp("list")))
    inspect_cap.list_archives.assert_called_once()

    orchestrator.execute(BackupRequest(BackupOp("help")))
    inspect_cap.help.assert_called_once()

    orchestrator.execute(BackupRequest(BackupOp("status")))
    inspect_cap.status.assert_called_once()

def test_backup_cli_maps_typed_outcomes_to_exit_codes(tmp_path):
    """The CLI surface renders aggregate outcomes, not by coercing the object."""
    from unittest.mock import MagicMock

    from modules.cli.src.surface_backup_command import cmd_backup, cmd_restore
    from modules.shared.src.backup.taxonomy_backup_vo import (
        BackupOutcome,
        BackupValue,
    )

    aggregate = MagicMock()
    aggregate.execute.return_value = BackupOutcome(
        success=True, tool_id="scratch", result=BackupValue(None)
    )
    destination = tmp_path / "custom-backups"
    assert cmd_backup(["backup", "scratch", str(destination)], aggregate) == 0
    request = aggregate.execute.call_args.args[0]
    assert str(request.dest) == str(destination)

    aggregate.execute.return_value = BackupOutcome(
        success=False, tool_id="scratch", result=BackupValue(None)
    )
    assert cmd_backup(["scratch"], aggregate) == 1
    assert cmd_restore(["restore", "scratch", "missing.tar.gz"], aggregate) == 1
