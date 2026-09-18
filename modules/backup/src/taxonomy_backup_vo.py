"""Backup-domain value objects for the AES backup feature."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BackupResult:
    """Outcome of a backup operation for one tool."""

    success: bool
    tool_id: str
    archive: str
    uploaded: bool
    message: str


@dataclass(frozen=True)
class RestoreResult:
    """Outcome of a restore operation for one tool."""

    success: bool
    tool_id: str
    archive: str
    target: str
    message: str
