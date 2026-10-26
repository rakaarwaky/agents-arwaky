"""Backup inspect capability (AES capabilities layer) — read-only store ops.

``TarBackupInspect`` implements ``IBackupInspectProtocol`` (list / status /
help) over the tar backup store. The tar/untar engine and its ``cmd_*``
helpers live in ``capabilities_backup_tar`` (control seam); this file
imports only that module's helper functions, never the control class, so
the two capabilities share helpers without a capability→capability edge.
"""
from __future__ import annotations

from modules.shared.src.backup.contract_backup_protocol import IBackupInspectProtocol
from modules.shared.src.backup.taxonomy_backup_constant import BACKUP_STORE
from modules.shared.src.backup.taxonomy_backup_vo import (
    BackupOutcome,
    ExitCode,
)

__all__ = ["TarBackupInspect", "cmd_help", "cmd_list"]


def cmd_list():
    """Print available backup archives to stdout."""
    print("Available backup archives:")
    archives = sorted(BACKUP_STORE.glob("*.tar.gz")) if BACKUP_STORE.exists() else []
    if not archives:
        print("  (none found — create one with 'aa backup <tool|all>')")
    for f in archives:
        print(f"  {f.name}")
    return 0


def cmd_help() -> int:
    """Print backup usage information to stdout."""
    print("Usage: aa backup <tool|all> [destination-dir]")
    print("       aa restore <tool|all> <archive.tar.gz>")
    print("       aa backup list")
    return 0


# ─── Block 1: Class Definition & Constructor ──────────────
class TarBackupInspect(IBackupInspectProtocol):
    """Read-only backup store ops: list / status / help."""

    # ─── Block 2: Protocol Method Implementation ──────────────
    def list_archives(self) -> BackupOutcome:
        """Return the archives visible to this gateway plus their print lines."""
        lines = cmd_list()
        return BackupOutcome(success=True, tool_id="", result=ExitCode(lines))

    def status(self) -> ExitCode:
        """Report the backup store path, existence, and archive count."""
        exists = BACKUP_STORE.is_dir()
        count = len(list(BACKUP_STORE.glob("*.tar.gz"))) if exists else 0
        print(f"Backup store: {BACKUP_STORE}")
        print(f"  exists: {'yes' if exists else 'no'}")
        print(f"  archives: {count}")
        return ExitCode(0)

    def help(self) -> ExitCode:
        """Show backup usage information."""
        return ExitCode(cmd_help())

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "TarBackupInspect()"
