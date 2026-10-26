"""Unit tests for modules/backup — test individual functions and methods."""
from __future__ import annotations

import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from modules.shared.src.backup.taxonomy_backup_vo import (
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
        from modules.backup.src.capabilities_backup_inspect import TarBackupInspect

        inspect_cap = TarBackupInspect()
        with patch("modules.backup.src.capabilities_backup_inspect.cmd_list", return_value=0):
            result = inspect_cap.list_archives()
            assert result.success is True
            assert result.result == 0

class TestBackupOrchestrator:
    """Tests for BackupOrchestrator class."""

    def test_init_creates_orchestrator(self):
        """UT-BACKUP-005: BackupOrchestrator initializes correctly."""
        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
        from modules.backup.src.capabilities_backup_inspect import TarBackupInspect
        from modules.backup.src.capabilities_backup_tar import TarBackupGateway

        tar = TarBackupGateway()
        orchestrator = BackupOrchestrator(tar, TarBackupInspect())
        assert orchestrator is not None

    def test_execute_list_delegates_to_tar(self):
        """UT-BACKUP-006: execute(list) routes to the inspect capability's list_archives."""
        from unittest.mock import MagicMock

        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

        tar = MagicMock()
        inspect_cap = MagicMock()
        inspect_cap.list_archives.return_value = BackupOutcome(success=True, tool_id="", result=0)
        orchestrator = BackupOrchestrator(tar, inspect_cap)

        response = orchestrator.execute(BackupRequest(BackupOp("list")))
        inspect_cap.list_archives.assert_called_once()
        assert response.result == 0

    def test_execute_help_delegates_to_tar(self):
        """UT-BACKUP-007: execute(help) routes to the inspect capability's help."""
        from unittest.mock import MagicMock

        from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

        tar = MagicMock()
        inspect_cap = MagicMock()
        inspect_cap.help.return_value = 0
        orchestrator = BackupOrchestrator(tar, inspect_cap)

        response = orchestrator.execute(BackupRequest(BackupOp("help")))
        inspect_cap.help.assert_called_once()
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

    def test_backup_store_path(self):
        """UT-BACKUP-012: BACKUP_STORE is a valid Path."""
        from modules.backup.src.capabilities_backup_tar import BACKUP_STORE

        assert BACKUP_STORE is not None
        assert isinstance(BACKUP_STORE, Path)

class TestTarBackupArchiveSafety:
    """Regression tests for non-overwrite and partial-archive guarantees."""

    def test_tar_dir_does_not_overwrite_existing_archive(self, tmp_path):
        import modules.backup.src.capabilities_backup_tar as backup_module

        source = tmp_path / "source"
        source.mkdir()
        (source / "state.txt").write_text("new", encoding="utf-8")
        archive = tmp_path / "existing.tar.gz"
        archive.write_bytes(b"preserve existing content")

        with pytest.raises(FileExistsError):
            backup_module.tar_dir(source, archive)
        assert archive.read_bytes() == b"preserve existing content"

    def test_tar_dir_removes_partial_archive_on_failure(self, tmp_path, monkeypatch):
        import modules.backup.src.capabilities_backup_tar as backup_module

        source = tmp_path / "source"
        source.mkdir()
        (source / "state.txt").write_text("new", encoding="utf-8")
        archive = tmp_path / "partial.tar.gz"

        class FailingTar:
            def __enter__(self):
                archive.write_bytes(b"partial")
                return self

            def __exit__(self, *_args):
                return False

            def add(self, *_args, **_kwargs):
                raise tarfile.TarError("simulated write failure")

        monkeypatch.setattr(backup_module.tarfile, "open", lambda *_args, **_kwargs: FailingTar())
        with pytest.raises(tarfile.TarError, match="simulated write failure"):
            backup_module.tar_dir(source, archive)
        assert not archive.exists()

    def test_archive_timestamp_collisions_get_unique_names(self, tmp_path, monkeypatch):
        import modules.backup.src.capabilities_backup_tar as backup_module

        source = tmp_path / "data" / "scratch"
        source.mkdir(parents=True)
        (source / "state.txt").write_text("state", encoding="utf-8")
        store = tmp_path / "backups"
        monkeypatch.setattr(backup_module, "data_home", lambda: tmp_path / "data")
        monkeypatch.setattr(backup_module, "BACKUP_STORE", store)

        class FixedDateTime:
            @staticmethod
            def now(_timezone):
                from datetime import datetime as RealDateTime

                return RealDateTime(2026, 10, 26, 12, 0, 0)

        monkeypatch.setattr(backup_module, "datetime", FixedDateTime)
        first = backup_module.backup_tool_result("scratch")
        second = backup_module.backup_tool_result("scratch")

        assert first.success and second.success
        assert first.archive != second.archive
        assert Path(first.archive).is_file() and Path(second.archive).is_file()
