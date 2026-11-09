"""Observability agent (AES agent layer).

Implements ``ISkillsObservabilityAggregate`` over the observability-side capabilities:
ledger, telemetry. Owns the ops: ledger, usage.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import cast

from observability.contract_observability_aggregate import ISkillsObservabilityAggregate
from shared.src.design.contract_skills_protocol import (
    ISkillsLedgerProtocol,
    ISkillsTelemetryProtocol,
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

from observability.capabilities_skills_ledger import SkillsLedger
from observability.capabilities_skills_telemetry import SkillsTelemetry

__all__ = [
    "SkillsObservabilityAgent",
    "ISkillsObservabilityAggregate",
]


class SkillsObservabilityAgent(ISkillsObservabilityAggregate):
    """Observability-side agent: ledger / usage."""

    def __init__(
        self,
        ledger: SkillsLedger | None = None,
        telemetry: SkillsTelemetry | None = None,
        default_root: SkillsRoot | None = None,
    ) -> None:
        self._ledger = ledger if ledger is not None else SkillsLedger()
        self._telemetry = telemetry if telemetry is not None else SkillsTelemetry()
        self._default_root = default_root

    # ─── Block 1: helpers ────────────────────────────────────────
    def _require(self, capability: object, name: str) -> object:
        if capability is None:
            raise SkillsRootError(f"observability capability not wired: {name}")
        return capability

    def _root(self, request: SkillsRequest) -> Path:
        if request.root:
            return Path(request.root)
        if self._default_root is not None:
            return Path(self._default_root)
        return Path()

    # ─── Block 2: Module Contract ────────────────
    def execute(self, request: SkillsRequest) -> SkillsResult:
        """Route *request* to the matching observability capability."""
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
    def _execute_ledger(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """LEDGER: append an entry to the audit ledger."""
        ledger = self._require(self._ledger, "ledger")
        root = self._root(request)
        entry = {
            "action": str(request.flags.get("action", "patch")),
            "skill": str(request.query or ""),
            "before": request.flags.get("before", []),
            "after": request.flags.get("after", []),
            "evidence": request.flags.get("evidence", {}),
        }
        try:
            result = ledger.ledger_append(root, entry)
        except OSError as failure:
            return SkillsResult(
                ok=False,
                op=op,
                exit_code=SkillsExitCode.ISSUES_FOUND,
                message=str(failure),
            )
        return SkillsResult(ok=True, op=op, message=str(result))

    def _execute_usage(self, request: SkillsRequest, op: SkillsOp) -> SkillsResult:
        """USAGE: bump/report per-skill telemetry sidecar."""
        telemetry = self._require(self._telemetry, "telemetry")
        root = self._root(request)
        verb = request.flags.get("verb", "report")
        skill = str(request.query or "")
        if verb == "seed":
            telemetry.seed_record_if_missing(skill, root)
            return SkillsResult(ok=True, op=op, message=f"seeded {skill}")
        if verb == "reanchor":
            telemetry.reanchor_clock(skill, root)
            return SkillsResult(ok=True, op=op, message=f"reanchored {skill}")
        report = telemetry.report(root)
        return SkillsResult(ok=True, op=op, records=report, root=root)

    def record_view(self, skill: str, root: SkillsRoot | None = None) -> None:
        """Public seam: bump the ``views`` counter for *skill* in ``.usage.json``."""
        telemetry = self._require(self._telemetry, "telemetry")
        target_root = root if root is not None else self._root(
            SkillsRequest(op=SkillsOp.USAGE, query=SkillQuery(skill or ""))
        )
        telemetry.view(skill, target_root)

    def show_skill(self, name: str, root: SkillsRoot | None = None):
        """Observability agent does not expose show_skill."""
        raise NotImplementedError("observability agent does not expose show_skill")