"""Backup feature — public symbols.

Re-exports the orchestrator, gateways, and verb entry points so feature
consumers can import from ``modules.backup`` directly. The composition
root (``root_backup_container``) is imported by callers directly, not
re-exported here, to keep the agent/capability package free of a root
re-export cycle (AES205).
"""
from __future__ import annotations

from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
from modules.backup.src.agent_backup_verb import cmd_backup, cmd_restore
from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway
from modules.backup.src.capabilities_backup_tar import TarBackupGateway

__all__ = [
    "BackupOrchestrator",
    "GdriveBackupGateway",
    "TarBackupGateway",
    "cmd_backup",
    "cmd_restore",
]
