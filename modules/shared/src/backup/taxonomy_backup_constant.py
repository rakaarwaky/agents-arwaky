"""Backup-domain constants — tool -> XDG data-subdir mapping (AES layer: taxonomy).

Pure compile-time data plus the resolved path anchors the tar gateway
shares: the local archive store and the repository root.
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

#: Local archive store the tar gateway writes to.
BACKUP_STORE: Path = data_home() / "backups"

#: Repository root.
ROOT: Path = REPO_ROOT

__all__ = [
    "BACKUP_STORE",
    "ROOT",
    "TOOL_DATA",
]