"""Maintenance agent (AES agent layer).

Implements ``ISkillsMaintenanceAggregate`` over the maintenance-side capabilities:
prune, purge. Owns the ops: prune, purge.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

from maintenance.contract_maintenance_aggregate import ISkillsMaintenanceAggregate
from shared.src.design.contract_skills_protocol import (
    ISkillsPruneProtocol,
    ISkillsPurgeProtocol,
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

from maintenance.capabilities_skills_prune import SkillsPrune
from maintenance.capabilities_skills_purge import SkillsPurge

__all__ = [
    "SkillsMaintenanceAgent",
    "ISkillsMaintenanceAggregate",
]


class SkillsMaintenanceAgent(ISkillsMaintenanceAggregate):
    """Maintenance-side agent: prune / purge."""

    def __init__(
        self,
        prune: SkillsPrune | None = None,
        purge: SkillsPurge | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._prune = prune if prune is not None else SkillsPrune()
        self._purge = purge if purge is not None else SkillsPurge()
        self._default_root = default_root

    # ─── Block 1: helpers ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"maintenance capability not wired: {name}")
        return capability

    def _root(self, request: SkillsRequest) -> Path:
        if request.root:
            return Path(request.root)
        if self._default_root is not None:
            return Path(self._default_root)
        return Path()

    # ─── Block 2: Module Contract ────────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching maintenance capability."""
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
    def _execute_prune(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """PRUNE: bulk-archive idle skills past a days threshold."""
        prune = self._require(self._prune, "prune")
        root = self._root(request)
        days = int(request.flags["days"]) if "days" in request.flags else None
        dry_run = bool(
            request.flags.get("dry_run", False) or request.flags.get("dry-run", False)
        )
        try:
            report = prune.prune(root=root, days=days, dry_run=dry_run)
        except (OSError, ValueError) as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, records=report.get("pruned", ()), message=str(report))

    def _execute_purge(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """PURGE: delete archived skills past TTL or a named skill."""
        purge = self._require(self._purge, "purge")
        root = self._root(request)
        query = str(request.query).strip() if request.query else ""
        skill_name = query if query and query != "None" else None
        dry_run = bool(
            request.flags.get("dry_run", False) or request.flags.get("dry-run", False)
        )
        try:
            result = purge.purge(skill=skill_name, root=root, dry_run=dry_run)
        except (OSError, ValueError) as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message=str(result))

    def show_skill(self, name: str, root: SkillsRoot | None = None):
        """Maintenance agent does not expose show_skill."""
        raise NotImplementedError("maintenance agent does not expose show_skill")