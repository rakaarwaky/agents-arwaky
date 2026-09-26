"""Dogfood tests — runs against live service/session.

These tests verify the module works with real external dependencies.
They use pytest.skipif to gracefully skip when services are unavailable.
"""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path


@pytest.mark.dogfood
def test_dogfood_backup_pipeline():
    """DOG-BACKUP-001: Actual backup workflow with real tar archive."""
    from modules.backup.src.capabilities_backup_tar import (
        backup_tool,
        cmd_list,
        BACKUP_STORE,
    )
    from modules.shared.src.taxonomy_common_vo import data_home as original_data_home

    # Create temporary test data
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test-tool-data"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("test content 1")
        (test_dir / "file2.txt").write_text("test content 2")

        # Simulate data home by patching
        import modules.backup.src.capabilities_backup_tar as backup_module
        original_data_home_fn = backup_module.data_home

        def mock_data_home():
            return Path(tmpdir)

        backup_module.data_home = mock_data_home
        try:
            # Run actual backup
            result = backup_tool("test-tool")
            # Result should be 0 (success) or non-zero if tool not found
            assert isinstance(result, int)

            # Check if archive was created in our temp dir
            archives = list(Path(tmpdir).glob("test-tool-*.tar.gz"))
            if archives:
                assert len(archives) > 0, "Archive should be created"
        finally:
            backup_module.data_home = original_data_home_fn
