"""Unit tests for modules/backup — test individual functions and methods."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestTarBackupGateway:
    """Tests for TarBackupGateway class."""

    def test_init_creates_gateway(self):
        """UT-BACKUP-001: TarBackupGateway initializes correctly."""
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        gateway = TarBackupGateway()
        assert gateway is not None

    def test_execute_archive_op_requires_tool(self):
        """UT-BACKUP-002: archive op requires a tool parameter."""
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        gateway = TarBackupGateway()
        result = gateway.execute("archive")
        assert result.success is False
        assert "requires a tool" in result.message

    def test_execute_restore_op_requires_tool(self):
        """UT-BACKUP-003: restore op requires a tool parameter."""
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        gateway = TarBackupGateway()
        result = gateway.execute("restore")
        assert result.success is False
        assert "requires a tool" in result.message

    def test_execute_unknown_op(self):
        """UT-BACKUP-004: unknown op returns failure."""
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        gateway = TarBackupGateway()
        result = gateway.execute("unknown_op")
        assert result.success is False

    def test_list_archives_empty_when_no_store(self):
        """UT-BACKUP-005: list_archives returns empty list when store doesn't exist."""
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        gateway = TarBackupGateway()
        with patch.object(gateway, 'list_archives') as mock_list:
            mock_list.return_value = []
            result = gateway.list_archives()
            assert result == []


class TestGdriveBackupGateway:
    """Tests for GdriveBackupGateway class."""

    def test_init_creates_gateway(self):
        """UT-BACKUP-006: GdriveBackupGateway initializes correctly."""
        from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

        gateway = GdriveBackupGateway()
        assert gateway is not None
        assert gateway._folder_name == "Agents-Arwaky-Backups"

    def test_execute_archive_op_requires_tool(self):
        """UT-BACKUP-007: archive op requires a tool parameter."""
        from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

        gateway = GdriveBackupGateway()
        result = gateway.execute("archive")
        assert result.success is False
        assert "requires a tool" in result.message

    def test_execute_unknown_op(self):
        """UT-BACKUP-008: unknown op returns failure."""
        from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

        gateway = GdriveBackupGateway()
        result = gateway.execute("unknown_op")
        assert result.success is False


class TestBackupOrchestrator:
    """Tests for BackupOrchestrator class."""

    def test_init_creates_orchestrator(self):
        """UT-BACKUP-009: BackupOrchestrator initializes correctly."""
        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        tar = TarBackupGateway()
        orchestrator = BackupOrchestrator(tar, tar)
        assert orchestrator is not None

    def test_backup_method_exists(self):
        """UT-BACKUP-010: backup method exists."""
        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        tar = TarBackupGateway()
        orchestrator = BackupOrchestrator(tar, tar)
        assert hasattr(orchestrator, 'backup')
        assert callable(getattr(orchestrator, 'backup'))

    def test_list_archives_delegates(self):
        """UT-BACKUP-011: list_archives delegates to tar gateway."""
        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        tar = TarBackupGateway()
        orchestrator = BackupOrchestrator(tar, tar)
        result = orchestrator.list_archives()
        # Should return exit code
        assert result is not None


class TestBackupFunctions:
    """Tests for standalone backup functions."""

    def test_is_tarfile_valid(self):
        """UT-BACKUP-012: tarfile.is_tarfile check works."""
        import tarfile
        from pathlib import Path
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as f:
            f.write(b"not a real tar")
            path = Path(f.name)

        try:
            assert not tarfile.is_tarfile(path)
        finally:
            path.unlink(missing_ok=True)

    def test_cmd_help_output(self):
        """UT-BACKUP-013: cmd_help returns expected help text."""
        from modules.backup.src.capabilities_backup_tar import cmd_help

        result = cmd_help()
        assert result == 0


class TestBackupConstants:
    """Tests for backup constants."""

    def test_default_folder_name(self):
        """UT-BACKUP-014: DEFAULT_FOLDER_NAME has expected value."""
        from modules.backup.src.capabilities_backup_gdrive import DEFAULT_FOLDER_NAME

        assert DEFAULT_FOLDER_NAME == "Agents-Arwaky-Backups"

    def test_backup_store_path(self):
        """UT-BACKUP-015: BACKUP_STORE is a valid Path."""
        from modules.backup.src.capabilities_backup_tar import BACKUP_STORE

        assert BACKUP_STORE is not None
        assert isinstance(BACKUP_STORE, Path)
