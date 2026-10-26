"""Backup surface — CLI adapters for aa backup / aa restore.

AES surface-layer command adapter: builds a typed ``BackupRequest`` from the
raw CLI tokens and calls the aggregate's single ``execute``; the agent
routes it to the right capability method. Rendering and token parsing
stay on the surface (AES406).
"""
from __future__ import annotations

from modules.shared.src.backup.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.backup.taxonomy_backup_vo import (
    BackupArchive,
    BackupDestination,
    BackupOp,
    BackupRequest,
    BackupToolQuery,
)


def _exit_code(response: object) -> int:
    """Translate a typed backup outcome to the process exit code."""
    return 0 if getattr(response, "success", False) else 1


def cmd_backup(args: list[str], orch: IBackupAggregate) -> int:
    """aa backup <tool|all> [destination-dir] | aa backup list | aa backup status."""
    # The root entry prepends the command noun; strip it so args[0] is the
    # first user token (tool / list / status / help) for both call shapes.
    if args and args[0] == "backup":
        args = args[1:]
    if not args or args[0] in ("help", "-h", "--help"):
        return _exit_code(orch.execute(BackupRequest(BackupOp("help"))))
    if args[0] == "list":
        return _exit_code(orch.execute(BackupRequest(BackupOp("list"))))
    if args[0] == "status":
        return _exit_code(orch.execute(BackupRequest(BackupOp("status"))))
    tool = BackupToolQuery(args[0])
    dest = BackupDestination(args[1] if len(args) > 1 else "")
    return _exit_code(
        orch.execute(BackupRequest(BackupOp("backup"), tool=tool, dest=dest))
    )


def cmd_restore(args: list[str], orch: IBackupAggregate) -> int:
    """aa restore <tool|all> [src] | aa restore help."""
    if args and args[0] == "restore":
        args = args[1:]
    if not args or args[0] in ("help", "-h", "--help"):
        return _exit_code(orch.execute(BackupRequest(BackupOp("help"))))
    tool = BackupToolQuery(args[0])
    archive = BackupArchive(args[1] if len(args) > 1 else "")
    return _exit_code(
        orch.execute(BackupRequest(BackupOp("restore"), tool=tool, archive=archive))
    )
