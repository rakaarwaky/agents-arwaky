"""Backup surface — CLI adapters for aa backup / aa restore.

AES surface-layer command adapter: one class implementing the aggregate
surface while staying free of root/capability imports (AES205).
"""
from __future__ import annotations


from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
from modules.shared.src.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.taxonomy_backup_vo import BackupToolQuery, ExitCode


class BackupCommand(IBackupAggregate):
    """CLI surface command for the backup feature (surface layer, AES406)."""

    def __init__(self, orch: BackupOrchestrator) -> None:
        self._orch = orch

    def backup(self, tool: BackupToolQuery, dest: str = "") -> ExitCode:
        return self._orch.backup(tool, dest)

    def restore(self, tool: BackupToolQuery, archive: str) -> ExitCode:
        return self._orch.restore(tool, archive)

    def list_archives(self) -> ExitCode:
        return self._orch.list_archives()

    def help(self) -> ExitCode:
        return self._orch.help()


def cmd_backup(args: list[str], orch: BackupOrchestrator) -> int:
    """aa backup <tool|all> [dest|gdrive] | aa backup list."""
    if not args or args[0] in ("help", "-h", "--help"):
        return orch.help()
    if args[0] == "list":
        return orch.list_archives()
    tool = BackupToolQuery(args[0])
    dest = args[1] if len(args) > 1 else ""
    return orch.backup(tool, dest)


def cmd_restore(args: list[str], orch: BackupOrchestrator) -> int:
    """aa restore <tool|all> [src] | aa restore help."""
    if not args or args[0] in ("help", "-h", "--help"):
        return orch.help()
    tool = BackupToolQuery(args[0])
    src = args[1] if len(args) > 1 else ""
    return orch.restore(tool, src)

