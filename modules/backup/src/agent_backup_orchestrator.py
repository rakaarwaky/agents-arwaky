"""Backup agent orchestrator — single-execute aggregate over the backup gateways.

Dispatches each ``BackupRequest.op`` to the matching rich protocol method on
the injected tar or gdrive gateway, then wraps the result in a
``BackupOutcome`` so the aggregate exposes exactly one entry point.
"""
from __future__ import annotations

from modules.shared.src.contract_backup_aggregate import IBackupAggregate
from modules.shared.src.contract_backup_protocol import IBackupProtocol
from modules.shared.src.taxonomy_backup_vo import (
    BackupDestination,
    BackupOp,
    BackupOutcome,
    BackupRequest,
    BackupResponse,
    BackupToolQuery,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class BackupOrchestrator(IBackupAggregate):
    """Single entry point over the backup gateways; dispatch happens here."""

    def __init__(self, tar_gateway: IBackupProtocol, gdrive_gateway: IBackupProtocol) -> None:
        self._tar = tar_gateway
        self._gdrive = gdrive_gateway

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: BackupRequest) -> BackupResponse:
        """Route *request* to the matching protocol method; return the response."""
        op = BackupOp(str(request.op))
        if op == "backup":
            gateway = self._gdrive if str(request.dest).startswith("gdrive") else self._tar
            result = gateway.backup(BackupToolQuery(str(request.tool)), BackupDestination(str(request.dest)))
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
            return BackupResponse(self._tar.list_archives())
        if op == "status":
            return BackupResponse(BackupOutcome(
                success=True,
                tool_id="",
                result=self._tar.status(),
            ))
        if op == "help":
            return BackupResponse(BackupOutcome(
                success=True,
                tool_id="",
                result=self._tar.help(),
            ))
        raise ValueError(f"Unknown backup op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "BackupOrchestrator()"


__all__ = ["BackupOrchestrator", "BackupRequest", "BackupResponse"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "BackupOrchestrator": BackupOrchestrator,
    "BackupRequest": BackupRequest,
    "BackupResponse": BackupResponse,
}
