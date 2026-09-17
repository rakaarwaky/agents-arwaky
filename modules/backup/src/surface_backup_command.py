"""Backup surface — CLI adapters for aa backup / aa restore."""
from __future__ import annotations

import sys

from modules.backup.src.agent_backup_orchestrator import BackupOrchestrator


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
    """aa restore <tool|all> <archive.tar.gz|backup-dir>."""
    if len(args) < 2:
        print("Usage: aa restore <tool|all> <archive.tar.gz|backup-dir>", file=sys.stderr)
        return 1
    return orch.restore(args[0], args[1])
