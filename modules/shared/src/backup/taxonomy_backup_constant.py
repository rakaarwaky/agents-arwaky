"""Backup-domain constants — tool -> XDG data-subdir mapping (AES layer: taxonomy).

Pure compile-time data plus the two resolved path anchors the gateways
share: the local archive store and the repository root.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_common_constant import REPO_ROOT
from modules.shared.src.taxonomy_common_vo import data_home

#: tool id -> XDG data subdirectory (relative to XDG_DATA_HOME) covered by backup.
TOOL_DATA: dict[str, str] = {
    "anytype": "anytype-mcp",
    "omniroute": "omniroute",
    "hindsight": "hindsight-memory",
    "google-workspace": "google-workspace-mcp",
}

#: Google Drive folder the gdrive gateway uploads archives into.
DEFAULT_FOLDER_NAME: str = "Agents-Arwaky-Backups"

#: Subprocess module spec for invoking the gdrive gateway from the tar gateway.
GDRIVE_HELPER: str = "-m:modules.backup.src.capabilities_backup_gdrive"

#: Local archive store the tar gateway writes and the gdrive gateway uploads.
BACKUP_STORE: Path = data_home() / "backups"

#: Repository root, shared by both gateways.
ROOT: Path = REPO_ROOT


__all__ = [
    "BACKUP_STORE",
    "DEFAULT_FOLDER_NAME",
    "GDRIVE_HELPER",
    "ROOT",
    "TOOL_DATA",
]
