"""Backup agent orchestrator — routes backup/restore across gateways."""
from __future__ import annotations

from modules.shared.src.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.contract_backup_protocol import IBackupProtocol
from modules.shared.src.taxonomy_backup_vo import (
    BackupDestination,
    BackupResult,
    BackupToolQuery,
    ExitCode,
    RestoreResult,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class BackupOrchestrator(IBackupAggregate):
    """Tar gateway first; list/status/help/restore-all stay on the tar gateway."""

    def __init__(self, tar_gateway: IBackupProtocol, gdrive_gateway: IBackupProtocol) -> None:
        self._tar = tar_gateway
        self._gdrive = gdrive_gateway

    # ─── Block 2: Aggregate Method Implementation ──────────
    def backup(self, tool: BackupToolQuery, dest: str = "") -> ExitCode:
        """Backup *tool* (or all tools); gdrive upload when dest starts with 'gdrive'."""
        gateway = self._gdrive if str(dest).startswith("gdrive") else self._tar
        result = gateway.execute("archive", tool, BackupDestination(dest))
        if isinstance(result, BackupResult) and result.success:
            return ExitCode(0)
        return ExitCode(1)

    def restore(self, tool: BackupToolQuery, archive: str) -> ExitCode:
        """Restore *tool* from a local archive, a backup dir, or gdrive."""
        result = self._tar.execute("restore", tool, archive=archive)
        if isinstance(result, RestoreResult) and result.success:
            return ExitCode(0)
        return ExitCode(1)

    def list_archives(self) -> ExitCode:
        return ExitCode(int(self._tar.execute("list_print") or 0))

    def status_store(self) -> ExitCode:
        """Report the backup store path, existence, and archive count (read-only)."""
        return ExitCode(int(self._tar.execute("status") or 0))

    def help(self) -> ExitCode:
        return ExitCode(int(self._tar.execute("help") or 0))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "BackupOrchestrator()"
