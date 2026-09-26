"""Backup-domain value objects for the AES backup feature.

The NewType identity VOs keep primitive ``str``/``int`` out of the
contract signatures (AES402), following the same pattern as
``modules.shared.src.taxonomy_tools_vo``. The request/response
envelopes (``BackupRequest`` / ``BackupResponse`` / ``BackupOutcome``)
let the aggregate keep a single ``execute`` entry point while the
protocol stays rich — one typed method per capability operation.
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

#: Module-level singleton for default archive argument (B008).
ARCHIVE_DEFAULT: BackupArchive = BackupArchive("")

#: Operation token dispatched by the aggregate's single ``execute``.
BackupOp = NewType("BackupOp", str)

#: Process exit code returned by a backup/restore/list/status/help action.
ExitCode = NewType("ExitCode", int)

#: Result payload of a single backup operation.
BackupValue = NewType("BackupValue", object)


@dataclass(frozen=True)
class BackupOutcome:
    """Single operation outcome: success flag, the tool that was acted on, and
    the typed payload (``BackupResult`` / ``RestoreResult`` / ``list[Path]`` /
    ``ExitCode`` / usage text)."""

    success: bool
    tool_id: str
    result: BackupValue


#: One backup request the surface/root/CLI hands to the aggregate.
@dataclass(frozen=True)
class BackupRequest:
    """Consumer verb envelope; ``op`` selects the protocol method the
    aggregate dispatches to (backup | restore | list | status | help)."""

    op: BackupOp
    tool: BackupToolQuery = BackupToolQuery("")
    dest: BackupDestination = DEST_DEFAULT
    archive: BackupArchive = ARCHIVE_DEFAULT


#: Response envelope returned by ``IBackupAggregate.execute``.
BackupResponse = NewType("BackupResponse", BackupOutcome)


__all__ = [
    "ARCHIVE_DEFAULT",
    "BackupArchive",
    "BackupDestination",
    "BackupOp",
    "BackupOutcome",
    "BackupRequest",
    "BackupResponse",
    "BackupResult",
    "BackupToolQuery",
    "BackupValue",
    "DEST_DEFAULT",
    "ExitCode",
    "RestoreResult",
]
