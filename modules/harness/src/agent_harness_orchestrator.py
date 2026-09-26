"""Harness agent orchestrator — the single agent for the harness feature.

Resolves raw CLI tokens (ids, aliases, ``--all``) to canonical harness ids
using the alias table in :mod:`taxonomy_harness_constant`, dedupes, and
surfaces unknown tokens to the CLI instead of raising. Each request is
dispatched to its capability's named protocol method; the adapter registry
is injected by the root layer.
"""
from __future__ import annotations

from modules.shared.src.contract_harness_aggregate import IHarnessAggregate
from modules.shared.src.contract_harness_protocol import IHarnessProtocol
from modules.shared.src.taxonomy_harness_constant import ALIASES, ALL_HARNESS_IDS
from modules.shared.src.taxonomy_harness_vo import (
    ExitCode,
    HarnessRequest,
    HarnessResponse,
    HarnessTargets,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class HarnessOrchestrator(IHarnessAggregate):
    """Resolve raw CLI tokens and route each request to its capability."""

    def __init__(
        self,
        connector: IHarnessProtocol,
        disconnector: IHarnessProtocol,
        skills: IHarnessProtocol,
    ) -> None:
        """Compose the three capabilities behind the orchestrator interface."""
        self._connector = connector
        self._disconnector = disconnector
        self._skills = skills

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: HarnessRequest) -> HarnessResponse:
        """Resolve the request's targets and route its op to its capability."""
        flags = request.flags or {}
        if request.op == "connect":
            code = self._connector.connect(
                self.resolve_targets(request.targets),
                force=flags.get("force", False),
                dry_run=flags.get("dry_run", False),
                mcp_only=flags.get("mcp_only", False),
                skills_only=flags.get("skills_only", False),
                env_only=flags.get("env_only", False),
                router=flags.get("router", False),
                copy_skills=flags.get("copy_skills", False),
            )
        elif request.op == "disconnect":
            code = self._disconnector.disconnect(
                self.resolve_targets(request.targets),
                dry_run=flags.get("dry_run", False),
            )
        elif request.op == "provision_skills":
            code = self._skills.provision_skills(
                self.resolve_targets(request.targets),
                copy=flags.get("copy", False),
                dry_run=flags.get("dry_run", False),
            )
        else:
            raise ValueError(f"HarnessOrchestrator does not handle op {request.op!r}")
        return HarnessResponse(exit_code=ExitCode(code))

    def resolve_targets(self, targets: HarnessTargets) -> HarnessTargets:
        """Map raw CLI tokens (id / alias / --all) onto canonical ids, deduped.

        Unknown tokens are DROPPED here; the CLI surface surfaces them
        before calling this method. ``--all`` expands to every supported id.
        """
        out: list[str] = []
        seen: set[str] = set()
        for target in targets:
            tid = ALIASES.get(target.lstrip("-"), target)
            if tid not in ALL_HARNESS_IDS or tid in seen:
                continue
            seen.add(tid)
            out.append(tid)
        return tuple(out)

    def all_targets(self) -> HarnessTargets:
        """Every supported harness id (canonical)."""
        return tuple(ALL_HARNESS_IDS)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "HarnessOrchestrator()"


__all__ = [
    "ExitCode",
    "HarnessOrchestrator",
    "HarnessRequest",
    "HarnessResponse",
    "IHarnessAggregate",
    "IHarnessProtocol",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "HarnessOrchestrator": HarnessOrchestrator,
    "HarnessRequest": HarnessRequest,
    "HarnessResponse": HarnessResponse,
    "IHarnessAggregate": IHarnessAggregate,
    "IHarnessProtocol": IHarnessProtocol,
}
