"""Backup surface — CLI adapters for aa backup / aa restore.

AES surface-layer command adapter: one class implementing the aggregate
surface while staying free of root/capability/agent imports (AES201/AES205).
"""
from __future__ import annotations

from modules.shared.src.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.taxonomy_backup_vo import BackupToolQuery, ExitCode


class BackupCommand(IBackupAggregate):
    """CLI surface command for the backup feature (surface layer, AES406)."""

    def __init__(self, orch: IBackupAggregate) -> None:
        self._orch = orch

    def backup(self, tool: BackupToolQuery, dest: str = "") -> ExitCode:
        return self._orch.backup(tool, dest)

    def restore(self, tool: BackupToolQuery, archive: str) -> ExitCode:
        return self._orch.restore(tool, archive)

    def list_archives(self) -> ExitCode:
        return self._orch.list_archives()

    def status_store(self) -> ExitCode:
        return self._orch.status_store()

    def help(self) -> ExitCode:
        return self._orch.help()


def cmd_backup(args: list[str], orch: IBackupAggregate) -> int:
    """aa backup <tool|all> [dest|gdrive] | aa backup list | aa backup status."""
    # The root entry prepends the command noun; strip it so args[0] is the
    # first user token (tool / list / status / help) for both call shapes.
    if args and args[0] == "backup":
        args = args[1:]
    if not args or args[0] in ("help", "-h", "--help"):
        return orch.help()
    if args[0] == "list":
        return orch.list_archives()
    if args[0] == "status":
        return orch.status_store()
    tool = BackupToolQuery(args[0])
    dest = args[1] if len(args) > 1 else ""
    return orch.backup(tool, dest)


def cmd_restore(args: list[str], orch: IBackupAggregate) -> int:
    """aa restore <tool|all> [src] | aa restore help."""
    if args and args[0] == "restore":
        args = args[1:]
    if not args or args[0] in ("help", "-h", "--help"):
        return orch.help()
    tool = BackupToolQuery(args[0])
    src = args[1] if len(args) > 1 else ""
    return orch.restore(tool, src)

