"""Backup agent orchestrator — single-execute aggregate over two backup subsystems.

Coordinates the two backup subsystems — the control seam (archive /
restore) and the inspect seam (list / status / help) — and dispatches each
``BackupRequest.op`` to the matching rich protocol method, wrapping the
result in a ``BackupOutcome`` so the aggregate exposes exactly one entry
point.
"""
from __future__ import annotations

from modules.shared.src.backup.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.backup.contract_backup_protocol import (
    IBackupControlProtocol,
    IBackupInspectProtocol,
)
from modules.shared.src.backup.taxonomy_backup_vo import (
    BackupDestination,
    BackupOp,
    BackupOutcome,
    BackupRequest,
    BackupResponse,
    BackupToolQuery,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class BackupOrchestrator(IBackupAggregate):
    """Coordinates the backup control and inspect subsystems; dispatch happens here."""

    def __init__(
        self,
        control: IBackupControlProtocol,
        inspect_cap: IBackupInspectProtocol,
    ) -> None:
        self._control = control
        self._inspect = inspect_cap

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: BackupRequest) -> BackupResponse:
        """Route *request* to the matching protocol method; return the response."""
        op = BackupOp(str(request.op))
        if op == "backup":
            result = self._control.backup(
                BackupToolQuery(str(request.tool)),
                BackupDestination(str(request.dest)),
            )
            return BackupResponse(
                BackupOutcome(
                    success=result.success,
                    tool_id=result.tool_id,
                    result=result,
                )
            )
        if op == "restore":
            result = self._control.restore(
                BackupToolQuery(str(request.tool)), request.archive
            )
            return BackupResponse(
                BackupOutcome(
                    success=result.success,
                    tool_id=result.tool_id,
                    result=result,
                )
            )
        if op == "list":
            result = self._inspect.list_archives()
            return BackupResponse(result)
        if op == "status":
            result = self._inspect.status()
            return BackupResponse(
                BackupOutcome(
                    success=result == 0,
                    tool_id="",
                    result=result,
                )
            )
        if op == "help":
            result = self._inspect.help()
            return BackupResponse(
                BackupOutcome(
                    success=result == 0,
                    tool_id="",
                    result=result,
                )
            )
        raise ValueError(f"unknown backup op: {op}")
