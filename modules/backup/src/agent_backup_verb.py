"""Backup surface — CLI adapters for aa backup / aa restore.

AES agent-layer verb class: one struct implementing the aggregate surface
(AES405) while staying free of root/capability imports (AES205).
"""
from __future__ import annotations


from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator
from modules.backup.src.contract_backup_aggregate import IBackupAggregate


class BackupVerb(IBackupAggregate):
    """CLI verb surface for the backup feature (agent layer, AES405)."""

    def __init__(self, orch: BackupOrchestrator) -> None:
        self._orch = orch

    def backup(self, tool: str, dest: str = "") -> int:
        return self._orch.backup(tool, dest)

    def restore(self, tool: str, archive: str) -> int:
        return self._orch.restore(tool, archive)

    def list_archives(self) -> int:
        return self._orch.list_archives()

    def help(self) -> int:
        return self._orch.help()


def cmd_backup(args: list[str], orch: BackupOrchestrator) -> int:
    """aa backup <tool|all> [dest|gdrive] | aa backup list."""
    if not args or args[0] in ("help", "-h", "--help"):
        return orch.help()
    if args[0] == "list":
        return orch.list_archives()
    tool = args[0]
    dest = args[1] if len(args) > 1 else ""
    return orch.backup(tool, dest)


def cmd_restore(args: list[str], orch: BackupOrchestrator) -> int:
    """aa restore <tool|all> [src] | aa restore help."""
    if not args or args[0] in ("help", "-h", "--help"):
        return orch.help()
    tool = args[0]
    src = args[1] if len(args) > 1 else ""
    return orch.restore(tool, src)
