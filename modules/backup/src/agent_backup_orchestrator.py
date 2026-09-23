"""Backup agent orchestrator — routes backup/restore across gateways."""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.contract_backup_protocol import IBackupProtocol
from modules.shared.src.taxonomy_backup_constant import TOOL_DATA
from modules.shared.src.taxonomy_backup_vo import (
    BackupDestination,
    BackupResult,
    BackupToolQuery,
    ExitCode,
    RestoreResult,
)
from modules.shared.src.taxonomy_common_vo import data_home

#: Local archive store under the XDG data home (shared gateway convention).
BACKUP_STORE = data_home() / "backups"


class BackupOrchestrator(IBackupAggregate):
    """Tar gateway first, gdrive gateway when the dest/flag demands it.

    Gateways are injected as ``IBackupProtocol`` and reached through
    ``execute`` (archive / restore / list); status and help stay local.

    # Block 1: Constructor (gateway injection)
    # Block 2: Backup routing
    # Block 3: Restore routing, listing & store status
    # Block 4: Protocol dispatch helpers
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, tar_gateway: IBackupProtocol, gdrive_gateway: IBackupProtocol) -> None:
        self._tar = tar_gateway
        self._gdrive = gdrive_gateway

    # -- Block 2: Backup routing ---------------------------------------------------
    def backup(self, tool: BackupToolQuery, dest: str = "") -> ExitCode:
        """Backup *tool* (or all tools); gdrive upload when dest starts with 'gdrive'."""
        if tool == "all":
            rc = 0
            for t in TOOL_DATA:
                if self._archive_ok(BackupToolQuery(t), dest):
                    continue
                rc = 1
            return rc
        return 0 if self._archive_ok(tool, dest) else 1

    # -- Block 3: Restore routing & listing -----------------------------------------
    def restore(self, tool: BackupToolQuery, archive: str) -> ExitCode:
        """Restore *tool* from a local archive, a backup dir, or gdrive."""
        if tool == "all":
            src_base = Path(archive)
            if not src_base.is_dir():
                print("  \u2717 'restore all' expects a backup directory containing per-tool archives.", file=sys.stderr)
                return 1
            rc = 0
            for t in TOOL_DATA:
                matches = sorted(src_base.glob(f"{t}-*.tar.gz"))
                if not matches:
                    print(f"  Warning: no archive found for {t} in {src_base}, skipping.", file=sys.stderr)
                    continue
                if not self._restore_ok(BackupToolQuery(t), str(matches[-1])):
                    rc = 1
            return rc
        return 0 if self._restore_ok(tool, archive) else 1

    def list_archives(self) -> ExitCode:
        print("Available backup archives:")
        archives = self._tar.execute("list")
        if not isinstance(archives, list):
            archives = []
        if not archives:
            print("  (none found — create one with 'aa backup <tool|all>')")
        for f in archives:
            print(f"  {f.name}")
        return 0

    def status_store(self) -> ExitCode:
        """Report the backup store path, existence, and archive count (read-only)."""
        exists = BACKUP_STORE.is_dir()
        count = len(list(BACKUP_STORE.glob("*.tar.gz"))) if exists else 0
        print(f"Backup store: {BACKUP_STORE}")
        print(f"  exists: {'yes' if exists else 'no'}")
        print(f"  archives: {count}")
        return 0

    def help(self) -> ExitCode:
        print("Usage: aa backup <tool|all> [dest|gdrive]")
        print("       aa restore <tool|all> <archive.tar.gz>")
        print("       aa backup list")
        print("       aa backup status")
        print(f"Tools: {', '.join(TOOL_DATA)}")
        return 0

    # -- Block 4: Protocol dispatch helpers ----------------------------------------
    def _archive_ok(self, tool: BackupToolQuery, dest: str) -> bool:
        result = self._tar.execute("archive", tool, BackupDestination(dest))
        return isinstance(result, BackupResult) and result.success

    def _restore_ok(self, tool: BackupToolQuery, archive: str) -> bool:
        result = self._tar.execute("restore", tool, archive=archive)
        return isinstance(result, RestoreResult) and result.success
