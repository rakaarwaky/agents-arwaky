"""Backup agent orchestrator — single-execute aggregate over the tar backup gateway.

Dispatches each ``BackupRequest.op`` to the matching rich protocol method on
the injected tar gateway, then wraps the result in a
``BackupOutcome`` so the aggregate exposes exactly one entry point.
"""
from __future__ import annotations

from modules.shared.src.backup.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.backup.contract_backup_protocol import IBackupProtocol
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
    """Single entry point over the tar backup gateway; dispatch happens here."""

    def __init__(self, tar_gateway: IBackupProtocol) -> None:
        self._tar = tar_gateway

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: BackupRequest) -> BackupResponse:
        """Route *request* to the matching protocol method; return the response."""
        op = BackupOp(str(request.op))
        if op == "backup":
            result = self._tar.backup(BackupToolQuery(str(request.tool)), BackupDestination(str(request.dest)))
            return BackupResponse(BackupOutcome(
                success=result.success,
                tool_id=result.tool_id,
                result=result,
            ))
        if op == "restore":
            result = self._tar.restore(BackupToolQuery(str(request.tool)), request.archive)
            return BackupResponse(BackupOutcome(
                success=result.success,
                tool_id=result.tool_id,
                result=result,
            ))
        if op == "list":
            result = self._tar.list_archives()
            return BackupResponse(result)
        if op == "status":
            result = self._tar.status()
            return BackupResponse(BackupOutcome(
                success=result == 0,
                tool_id="",
                result=result,
            ))
        if op == "help":
            result = self._tar.help()
            return BackupResponse(BackupOutcome(
                success=result == 0,
                tool_id="",
                result=result,
            ))
        raise ValueError(f"unknown backup op: {op}")