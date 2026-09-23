"""Backup-domain value objects for the AES backup feature.

`BackupToolQuery` and `ExitCode` keep primitive `str`/`int` out of the
contract signatures (AES402), following the same NewType identity-VO
pattern as `modules.shared.src.taxonomy_tools_vo`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType


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


#: Manifest / CLI tool identifier accepted by a backup/restore call.
BackupToolQuery = NewType("BackupToolQuery", str)

#: Destination descriptor (e.g. "gdrive" or local path) for backup archives.
BackupDestination = NewType("BackupDestination", str)

#: Module-level singleton for default argument (B008).
DEST_DEFAULT: BackupDestination = BackupDestination("")

#: Archive path or identifier string for restore operations.
BackupArchive = NewType("BackupArchive", str)

#: Process exit code returned by a backup/restore/list/help action.
ExitCode = NewType("ExitCode", int)

__all__ = [
    "DEST_DEFAULT",
    "BackupArchive",
    "BackupDestination",
    "BackupResult",
    "BackupToolQuery",
    "ExitCode",
    "RestoreResult",
]
