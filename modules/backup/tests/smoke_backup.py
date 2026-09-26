"""Smoke tests for modules/backup — fast import and basic checks."""
from __future__ import annotations

import time


def test_import_backup_modules():
    """SM-BACKUP-001: Backup modules can be imported."""
    from modules.backup.src import capabilities_backup_tar
    from modules.backup.src import capabilities_backup_gdrive
    from modules.backup.src import agent_backup_orchestrator
    from modules.backup.src import root_backup_container

    assert capabilities_backup_tar is not None
    assert capabilities_backup_gdrive is not None
    assert agent_backup_orchestrator is not None
    assert root_backup_container is not None


def test_gateway_init_quick():
    """SM-BACKUP-002: Gateway initialization is quick."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway

    start = time.time()
    tar = TarBackupGateway()
    gdrive = GdriveBackupGateway()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_orchestrator_init_quick():
    """SM-BACKUP-003: Orchestrator initialization is quick."""
    from modules.backup.src.capabilities_backup_tar import TarBackupGateway
    from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator

    start = time.time()
    tar = TarBackupGateway()
    orch = BackupOrchestrator(tar, tar)
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_container_creation_quick():
    """SM-BACKUP-004: Container creation is quick."""
    from modules.backup.src.root_backup_container import BackupContainer

    start = time.time()
    container = BackupContainer()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Container creation took {elapsed:.2f}s"
