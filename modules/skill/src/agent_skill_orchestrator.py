"""Skill agent orchestrator — single-execute aggregate over registry + provisioner.

Routes each ``SkillRequest.op`` to the matching capability role (registry or
provisioner) and wraps the result in a ``SkillResponse``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from modules.shared.src.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.contract_skill_protocol import (
    ISkillProvisionProtocol,
    ISkillRegistryProtocol,
)
from modules.shared.src.taxonomy_common_vo import PackFinding
from modules.shared.src.taxonomy_skill_vo import (
    ARGS_EMPTY,
    FILTER_EMPTY,
    QUERY_EMPTY,
    ExitCode,
    SkillArgs,
    SkillOp,
    SkillRequest,
    SkillResponse,
    SkillQuery,
    ToolFilter,
)


class _SkillRegistry(Protocol):
    """Registry surface the orchestrator drives (named ops beyond ``execute``)."""

    def list(self, tool_filter: ToolFilter = FILTER_EMPTY) -> ExitCode: ...
    def check(self) -> ExitCode: ...
    def show(self, query: SkillQuery = QUERY_EMPTY) -> ExitCode: ...
    def install(self, args: SkillArgs) -> ExitCode: ...
    def uninstall(self, args: SkillArgs) -> ExitCode: ...
    def sync(self, args: SkillArgs) -> ExitCode: ...


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillOrchestrator(ISkillAggregate):
    """Single entry point over the skill feature; dispatch happens here."""

    def __init__(
        self,
        provisioner: ISkillProvisionProtocol,
        registry: ISkillRegistryProtocol | _SkillRegistry,
    ) -> None:
        self._provisioner = provisioner
        self._registry = registry

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: SkillRequest) -> SkillResponse:
        """Route *request* to the matching capability role; return the response."""
        op = SkillOp(str(request.op))
        if op in {"list"}:
            result = self._registry.list(
                ToolFilter(str(request.tool_filter)) if request.tool_filter != FILTER_EMPTY else FILTER_EMPTY
            )
            return SkillResponse(result)
        if op == "check":
            return SkillResponse(self._registry.check())
        if op == "show":
            return SkillResponse(
                self._registry.show(SkillQuery(str(request.query)) if request.query else QUERY_EMPTY)
            )
        if op in {"install", "uninstall", "sync"}:
            args = SkillArgs(list(request.args) if request.args else [])
            result = getattr(self._registry, op)(args)
            return SkillResponse(result)
        if op in {"provision", "prune", "audit"}:
            target = request.target if request.target is not None else Path.cwd()
            if op == "provision":
                result = self._provisioner.provision(
                    ToolFilter(str(request.tool_filter)) if request.tool_filter else FILTER_EMPTY,
                    target,
                    custom_dest=request.custom_dest,
                    force=request.force,
                    link=request.link,
                    prune=request.prune,
                )
                return SkillResponse(ExitCode(0 if result.success else 1))
            if op == "prune":
                result = self._provisioner.prune(target, custom_dest=request.custom_dest)
                return SkillResponse(ExitCode(0 if result.success else 1))
            if op == "audit":
                findings = self._provisioner.audit()
                return SkillResponse(ExitCode(1 if findings else 0), findings=tuple(findings))
        return SkillResponse(ExitCode(1))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "SkillOrchestrator()"


__all__ = [
    "ARGS_EMPTY",
    "FILTER_EMPTY",
    "QUERY_EMPTY",
    "ExitCode",
    "SkillArgs",
    "SkillOrchestrator",
    "SkillQuery",
    "ToolFilter",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ARGS_EMPTY": ARGS_EMPTY,
    "FILTER_EMPTY": FILTER_EMPTY,
    "QUERY_EMPTY": QUERY_EMPTY,
    "ExitCode": ExitCode,
    "SkillArgs": SkillArgs,
    "SkillOrchestrator": SkillOrchestrator,
    "SkillQuery": SkillQuery,
    "ToolFilter": ToolFilter,
}
