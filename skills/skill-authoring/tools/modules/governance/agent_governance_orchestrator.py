"""Governance agent (AES agent layer).

Implements ``ISkillsGovernanceAggregate`` over the governance-side capabilities:
locker, piner, mover. Owns the ops: lock, unlock, pin, unpin, move.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from shared.src.common.taxonomy_common_error import (
    SkillsError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.design.contract_skills_protocol import (
    ISkillsLockerProtocol,
    ISkillsMoverProtocol,
    ISkillsPinerProtocol,
)
from shared.src.design.taxonomy_skills_request import (
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)
from shared.src.governance.contract_governance_aggregate import (
    ISkillsGovernanceAggregate,
)

__all__ = [
    "ISkillsGovernanceAggregate",
    "SkillsGovernanceAgent",
]


class SkillsGovernanceAgent(ISkillsGovernanceAggregate):
    """Governance-side agent: lock / unlock / pin / unpin / move."""

    def __init__(
        self,
        locker: ISkillsLockerProtocol | None = None,
        piner: ISkillsPinerProtocol | None = None,
        mover: ISkillsMoverProtocol | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._locker = locker
        self._piner = piner
        self._mover = mover
        self._default_root = default_root

    # ─── Block 1: Module Declaration ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"governance capability not wired: {name}")
        return capability

    def _root(self, request: SkillsRequest) -> SkillsRoot | None:
        if request.root:
            return request.root
        return self._default_root

    def _mutate_skill(
        self,
        request: SkillsRequest,
        op: SkillsOp,
        capability: object,
        verb: str,
        field: str,
        value: object,
    ) -> SkillsResult:
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
            result = getattr(capability, verb)(skill_name, root)
        except (OSError, ValueError, SkillsUsageError) as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message=str(result))

    # ─── Block 2: Module Contract ────────────────────────────────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching governance capability."""
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

    # ─── Block 3: Module Helpers ────────────────────────────────────────
    def _execute_move(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """MOVE: plan/apply a skill to another category."""
        mover = self._require(self._mover, "mover")
        root = self._root(request)
        if not request.query or str(request.query).strip() in ("", "None"):
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message="Skill name required",
            )
        skill_name = str(request.query).strip()
        target = request.flags.get("target") or request.flags.get("category")
        if not target:
            raise SkillsUsageError("Missing --target: pass --target <category>")
        apply = request.apply
        if apply:
            plan = mover.plan_move(skill_name, target, root)
            outcome = mover.apply_move(plan)
            return SkillsResult(
                ok=True,
                op=op,
                plan=plan,
                outcome=outcome,
                root=root,
                message=str(outcome.message),
            )
        plan = mover.plan_move(skill_name, target, root)
        return SkillsResult(ok=True, op=op, plan=plan, root=root, message=str(plan.kind))

    def _execute_lock(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """LOCK: set locked=True on skill sidecar."""
        locker = self._require(self._locker, "locker")
        return self._mutate_skill(request, op, locker, "lock", "locked", True)

    def _execute_unlock(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """UNLOCK: set locked=False on skill sidecar."""
        locker = self._require(self._locker, "locker")
        return self._mutate_skill(request, op, locker, "unlock", "locked", False)

    def _execute_pin(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """PIN: set pinned=True on skill sidecar."""
        piner = self._require(self._piner, "piner")
        return self._mutate_skill(request, op, piner, "pin", "pinned", True)

    def _execute_unpin(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """UNPIN: set pinned=False on skill sidecar."""
        piner = self._require(self._piner, "piner")
        return self._mutate_skill(request, op, piner, "unpin", "pinned", False)

    def show_skill(self, name: str, root: SkillsRoot | None = None) -> SkillsResult:
        """Governance agent does not expose show_skill."""
        return SkillsResult(
            ok=False,
            op=SkillsOp.READ,
            exit_code=SkillsExitCode.USAGE_ERROR,
            message=f"governance agent does not expose show_skill for {name}",
        )
