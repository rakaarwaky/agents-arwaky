"""Unit tests for modules/backup — test individual functions and methods."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from modules.shared.src.taxonomy_backup_vo import (
    BackupOp,
    BackupOutcome,
    BackupRequest,
)


class TestTarBackupGateway:
    """Tests for TarBackupGateway class."""

    def test_init_creates_gateway(self):
        """UT-BACKUP-001: TarBackupGateway initializes correctly."""
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        gateway = TarBackupGateway()
        assert gateway is not None

    def test_list_archives_returns_outcome(self):
        """UT-BACKUP-002: list_archives wraps cmd_list's exit code in an outcome."""
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        gateway = TarBackupGateway()
        with patch("modules.backup.src.capabilities_backup_tar.cmd_list", return_value=0):
            result = gateway.list_archives()
            assert result.success is True
            assert result.result == 0


class TestGdriveBackupGateway:
    """Tests for GdriveBackupGateway class."""

    def test_init_creates_gateway(self):
        """UT-BACKUP-003: GdriveBackupGateway initializes correctly."""
        from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

        gateway = GdriveBackupGateway()
        assert gateway is not None
        assert gateway._folder_name == "Agents-Arwaky-Backups"

    def test_backup_without_local_archive_fails(self):
        """UT-BACKUP-004: backup reports failure when no local archive exists."""
        from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

        gateway = GdriveBackupGateway()
        with patch("modules.shared.src.taxonomy_common_vo.data_home") as mock_home:
            mock_home.return_value = Path("/nonexistent-store")
            result = gateway.backup("no-such-tool")
            assert result.success is False


class TestBackupOrchestrator:
    """Tests for BackupOrchestrator class."""

    def test_init_creates_orchestrator(self):
        """UT-BACKUP-005: BackupOrchestrator initializes correctly."""
        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        tar = TarBackupGateway()
        orchestrator = BackupOrchestrator(tar, tar)
        assert orchestrator is not None

    def test_execute_list_delegates_to_tar(self):
        """UT-BACKUP-006: execute(list) routes to the tar gateway's list_archives."""
        from unittest.mock import MagicMock

        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

        tar = MagicMock()
        tar.list_archives.return_value = BackupOutcome(success=True, tool_id="", result=[])
        orchestrator = BackupOrchestrator(tar, tar)

        response = orchestrator.execute(BackupRequest(BackupOp("list")))
        tar.list_archives.assert_called_once()
        assert response.result == []

    def test_execute_help_delegates_to_tar(self):
        """UT-BACKUP-007: execute(help) routes to the tar gateway's help."""
        from unittest.mock import MagicMock

        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

        tar = MagicMock()
        tar.help.return_value = 0
        orchestrator = BackupOrchestrator(tar, tar)

        response = orchestrator.execute(BackupRequest(BackupOp("help")))
        tar.help.assert_called_once()
        assert response.result == 0

    def test_execute_unknown_op_raises(self):
        """UT-BACKUP-008: an unknown op raises a typed error."""
        from unittest.mock import MagicMock

        import pytest

        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

        orchestrator = BackupOrchestrator(MagicMock(), MagicMock())
        with pytest.raises(ValueError):
            orchestrator.execute(BackupRequest(BackupOp("nope")))


class TestBackupFunctions:
    """Tests for standalone backup functions."""

    def test_is_tarfile_valid(self):
        """UT-BACKUP-009: tarfile.is_tarfile check works."""
        import tarfile

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as f:
            f.write(b"not a real tar")
            path = Path(f.name)

        try:
            assert not tarfile.is_tarfile(path)
        finally:
            path.unlink(missing_ok=True)
    def test_cmd_help_output(self):
        """UT-BACKUP-010: cmd_help returns expected help text."""
        from modules.backup.src.capabilities_backup_tar import cmd_help

        result = cmd_help()
        assert result == 0


class TestBackupConstants:
    """Tests for backup constants."""

    def test_default_folder_name(self):
        """UT-BACKUP-011: DEFAULT_FOLDER_NAME has expected value."""
        from modules.backup.src.capabilities_backup_gdrive import DEFAULT_FOLDER_NAME

        assert DEFAULT_FOLDER_NAME == "Agents-Arwaky-Backups"

    def test_backup_store_path(self):
        """UT-BACKUP-012: BACKUP_STORE is a valid Path."""
        from modules.backup.src.capabilities_backup_tar import BACKUP_STORE

        assert BACKUP_STORE is not None
        assert isinstance(BACKUP_STORE, Path)
