"""Backup agent orchestrator — routes backup/restore across gateways."""
from __future__ import annotations

from pathlib import Path

from modules.backup.src.capabilities_backup_gdrive import GdriveBackupGateway
from modules.backup.src.capabilities_backup_tar import TarBackupGateway, TOOL_DATA
from modules.shared.src.backup.contract_backup_aggregate import IBackupAggregate


class BackupOrchestrator(IBackupAggregate):
    """Tar gateway first, gdrive gateway when the dest/flag demands it.

    # Block 1: Constructor (gateway injection)
    # Block 2: Backup routing
    # Block 3: Restore routing & listing
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, tar_gateway: TarBackupGateway, gdrive_gateway: GdriveBackupGateway) -> None:
        self._tar = tar_gateway
        self._gdrive = gdrive_gateway

    # -- Block 2: Backup routing ---------------------------------------------------
    def backup(self, tool: str, dest: str = "") -> int:
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
    def restore(self, tool: str, archive: str) -> int:
        """Restore *tool* from a local archive, a backup dir, or gdrive."""
        import sys

        if tool == "all":
            src_base = Path(archive)
            if not src_base.is_dir():
                print(f"  \u2717 'restore all' expects a backup directory containing per-tool archives.", file=sys.stderr)
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

    def list_archives(self) -> int:
        print("Available backup archives:")
        archives = self._tar.list_archives()
        if not archives:
            print("  (none found — create one with 'aa backup <tool|all>')")
        for f in archives:
            print(f"  {f.name}")
        return 0

    def help(self) -> int:
        print("Usage: aa backup <tool|all> [dest|gdrive]")
        print("       aa restore <tool|all> <archive.tar.gz>")
        print("       aa backup list")
        print(f"Tools: {', '.join(TOOL_DATA)}")
        return 0
