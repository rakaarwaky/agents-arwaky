"""Storage agent (AES agent layer).

Implements ``ISkillsStorageAggregate`` over the storage-side capabilities:
archiver, backup, restore, rollback. Owns the ops: archive, restore,
backup, rollback.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

from storage.contract_storage_aggregate import ISkillsStorageAggregate
from shared.src.design.contract_skills_protocol import (
    ISkillsArchiverProtocol,
    ISkillsBackupProtocol,
    ISkillsRestoreProtocol,
    ISkillsRollbackProtocol,
)
from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsRootError,
)
from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)

from storage.capabilities_skills_archiver import SkillsArchiver
from storage.capabilities_skills_backup import SkillsBackup
from storage.capabilities_skills_restore import SkillsRestore
from storage.capabilities_skills_rollback import SkillsRollback

__all__ = [
    "SkillsStorageAgent",
    "ISkillsStorageAggregate",
]


class SkillsStorageAgent(ISkillsStorageAggregate):
    """Storage-side agent: archive / restore / backup / rollback."""

    def __init__(
        self,
        archiver: SkillsArchiver | None = None,
        backup: SkillsBackup | None = None,
        restore: SkillsRestore | None = None,
        rollback: SkillsRollback | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._archiver = archiver if archiver is not None else SkillsArchiver()
        self._backup = backup if backup is not None else SkillsBackup()
        self._restore = restore if restore is not None else SkillsRestore()
        self._rollback = (
            rollback if rollback is not None else SkillsRollback(self._backup)
        )
        self._default_root = default_root

    # ─── Block 1: helpers ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"storage capability not wired: {name}")
        return capability

    def _root(self, request: SkillsRequest) -> Path:
        if request.root:
            return Path(request.root)
        if self._default_root is not None:
            return Path(self._default_root)
        return Path()

    # ─── Block 2: Module Contract ────────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching storage capability."""
        try:
            op = SkillsOp(request.op)
        except ValueError:
            return SkillsResult(
                ok=False,
                op=SkillsOp.LIST,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown skills op: {request.op}",
            )

        try:
            handler = self._handler_for(op)
        except KeyError:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.USAGE_ERROR,
                message=f"Unknown skills op: {op}",
            )

        try:
            return handler(request, op)
        except SkillsError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=failure.exit_code,
                message=str(failure),
            )

    def _handler_for(
        self, op: SkillsOp
    ) -> Callable[[SkillsRequest, SkillsOp], SkillsResult]:
        name = f"_execute_{op.value.replace('-', '_')}"
        handler = getattr(self, name, None)
        if not callable(handler):
            raise KeyError(name)
        return cast(Callable[[SkillsRequest, SkillsOp], SkillsResult], handler)

    # ─── Block 3: per-op handlers ────────────────────────────────
    def _execute_archive(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """ARCHIVE: move a live skill into _archive/."""
        archiver = self._require(self._archiver, "archiver")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        try:
            result = archiver.archive(skill_name, root)
        except (OSError, SkillsError) as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message=str(result))

    def _execute_restore(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """RESTORE: restore an archived skill back to the live pack."""
        restore = self._require(self._restore, "restore")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        try:
            result = restore.restore(skill_name, root)
        except (OSError, SkillsError) as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message=str(result))

    def _execute_backup(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """BACKUP: create a content-addressed snapshot of the pack."""
        backup = self._require(self._backup, "backup")
        root = self._root(request)
        try:
            path = backup.create_snapshot(root)
        except OSError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message=str(path))

    def _execute_rollback(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """ROLLBACK: restore the pack tree from a stored snapshot."""
        rollback = self._require(self._rollback, "rollback")
        root = self._root(request)
        snapshot_id = request.flags.get("id") or request.query
        try:
            result = rollback.rollback(root, snapshot_id)
        except OSError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message=str(result))

    def show_skill(self, name: str, root: SkillsRoot | None = None):
        """Storage agent does not expose show_skill."""
        raise NotImplementedError("storage agent does not expose show_skill")