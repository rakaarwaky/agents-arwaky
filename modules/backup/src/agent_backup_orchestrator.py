"""Backup agent orchestrator — routes backup/restore across gateways."""
from __future__ import annotations

import sys
from pathlib import Path

from modules.shared.src.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.contract_backup_protocol import IBackupGateway
from modules.shared.src.taxonomy_backup_constant import TOOL_DATA
from modules.shared.src.taxonomy_backup_vo import BackupToolQuery, ExitCode


class BackupOrchestrator(IBackupAggregate):
    """Tar gateway first, gdrive gateway when the dest/flag demands it.

    # Block 1: Constructor (gateway injection)
    # Block 2: Backup routing
    # Block 3: Restore routing & listing
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, tar_gateway: IBackupGateway, gdrive_gateway: IBackupGateway) -> None:
        self._tar = tar_gateway
        self._gdrive = gdrive_gateway

    # -- Block 2: Backup routing ---------------------------------------------------
    def backup(self, tool: BackupToolQuery, dest: str = "") -> ExitCode:
        """Backup *tool* (or all tools); gdrive upload when dest starts with 'gdrive'."""
        if tool == "all":
            rc = 0
            for t in TOOL_DATA:
                if self._tar.backup(t, dest).success:
                    continue
                rc = 1
            return rc
        return 0 if self._tar.backup(tool, dest).success else 1

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
                if not self._tar.restore(t, matches[-1]).success:
                    rc = 1
            return rc
        return 0 if self._tar.restore(tool, Path(archive)).success else 1

    def list_archives(self) -> ExitCode:
        print("Available backup archives:")
        archives = self._tar.list_archives()
        if not archives:
            print("  (none found — create one with 'aa backup <tool|all>')")
        for f in archives:
            print(f"  {f.name}")
        return 0

    def help(self) -> ExitCode:
        print("Usage: aa backup <tool|all> [dest|gdrive]")
        print("       aa restore <tool|all> <archive.tar.gz>")
        print("       aa backup list")
        print(f"Tools: {', '.join(TOOL_DATA)}")
        return 0
