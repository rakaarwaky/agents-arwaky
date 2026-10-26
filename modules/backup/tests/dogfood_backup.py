"""Dogfood tests for real local tar archives and restore-ready backups."""
from __future__ import annotations

import tarfile
from pathlib import Path

import pytest


@pytest.mark.dogfood
def test_dogfood_backup_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DOG-BACKUP-001: actual backup creates a restorable local tar archive."""
    import modules.backup.src.capabilities_backup_tar as backup_module

    data = tmp_path / "data"
    tool_dir = data / "test-tool"
    tool_dir.mkdir(parents=True)
    (tool_dir / "file1.txt").write_text("test content 1", encoding="utf-8")
    (tool_dir / "file2.txt").write_text("test content 2", encoding="utf-8")
    store = tmp_path / "backups"
    monkeypatch.setattr(backup_module, "data_home", lambda: data)
    monkeypatch.setattr(backup_module, "BACKUP_STORE", store)

    result = backup_module.backup_tool_result("test-tool")

    assert result.success is True
    archive = Path(result.archive)
    assert archive.parent == store
    assert archive.is_file()
    with tarfile.open(archive, "r:gz") as tar:
        assert tar.extractfile("test-tool/file1.txt").read() == b"test content 1"
        assert tar.extractfile("test-tool/file2.txt").read() == b"test content 2"


@pytest.mark.dogfood
def test_dogfood_backup_all_registered_tools_to_local_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BKP-01 scope: archive every registered tool to a local destination."""
    import modules.backup.src.capabilities_backup_tar as backup_module
    from modules.shared.src.backup.taxonomy_backup_constant import TOOL_DATA

    data = tmp_path / "data"
    for subdir in TOOL_DATA.values():
        tool_dir = data / subdir
        tool_dir.mkdir(parents=True)
        (tool_dir / "state.txt").write_text(subdir, encoding="utf-8")
    store = tmp_path / "backups"
    monkeypatch.setattr(backup_module, "data_home", lambda: data)
    monkeypatch.setattr(backup_module, "BACKUP_STORE", store)

    result = backup_module.backup_tool_result("all", str(store))

    assert result.success is True
    assert len(list(store.glob("*.tar.gz"))) == len(TOOL_DATA)
    for archive in store.glob("*.tar.gz"):
        with tarfile.open(archive, "r:gz") as tar:
            assert len(tar.getmembers()) == 2


@pytest.mark.dogfood
def test_dogfood_root_cli_writes_only_to_local_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The root CLI routes backup requests through the local archive gateway."""
    import modules.backup.src.capabilities_backup_tar as backup_module
    from modules.root_cli_entry import cmd_backup

    data = tmp_path / "data"
    tool_dir = data / "scratch"
    tool_dir.mkdir(parents=True)
    (tool_dir / "state.txt").write_text("local backup", encoding="utf-8")
    store = tmp_path / "custom-backups"
    monkeypatch.setattr(backup_module, "data_home", lambda: data)
    monkeypatch.setattr(backup_module, "BACKUP_STORE", tmp_path / "default-backups")

    assert cmd_backup(["scratch", str(store)]) == 0
    archives = list(store.glob("*.tar.gz"))
    assert len(archives) == 1
    assert archives[0].is_file()
    assert not (tmp_path / "default-backups").exists()


@pytest.mark.dogfood
def test_dogfood_restore_recreates_a_fresh_tool_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BKP-03: a local archive restores into a fresh tool state directory."""
    import modules.backup.src.capabilities_backup_tar as backup_module

    data = tmp_path / "data"
    tool_dir = data / "scratch"
    tool_dir.mkdir(parents=True)
    (tool_dir / "settings.json").write_text('{"mode": "safe"}', encoding="utf-8")
    store = tmp_path / "backups"
    monkeypatch.setattr(backup_module, "data_home", lambda: data)
    monkeypatch.setattr(backup_module, "BACKUP_STORE", store)

    result = backup_module.backup_tool_result("scratch")
    assert result.success is True
    archive = Path(result.archive)
    assert archive.is_file()

    (tool_dir / "settings.json").unlink()
    tool_dir.rmdir()
    assert backup_module.restore_tool("scratch", str(archive)) == 0
    assert (tool_dir / "settings.json").read_text(encoding="utf-8") == '{"mode": "safe"}'
