"""Backup feature — public symbols.

Re-exports the orchestrator, container, gateways, and surface entry
points so feature consumers can import from ``modules.backup`` directly.
"""
from __future__ import annotations

from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway
from modules.backup.src.capabilities_backup_tar import TarBackupGateway
from modules.backup.src.root_backup_container import BackupContainer, create_backup_feature
from modules.cli.src.surface_backup_command import cmd_backup, cmd_restore

__all__ = [
    "BackupContainer",
    "BackupOrchestrator",
    "GdriveBackupGateway",
    "TarBackupGateway",
    "cmd_backup",
    "cmd_restore",
    "create_backup_feature",
]
