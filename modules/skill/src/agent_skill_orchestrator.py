"""Skill agent orchestrator — coordinates registry + pack provisioner.

Dispatches every surface action to the original command handlers, ported
as-is from tools/skill/skill.py into the registry adapter (injected as a
concrete capability object by the root composition layer).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.taxonomy_skill_vo import (
    FILTER_EMPTY,
    QUERY_EMPTY,
    ExitCode,
    SkillArgs,
    SkillProvisionResult,
    SkillQuery,
    ToolFilter,
)


class SkillOrchestrator(ISkillAggregate):
    """Routing of skill surface actions to the capabilities (original bodies).

    # Block 1: Constructor
    # Block 2: Query actions (list/check/show)
    # Block 3: Mutation actions (install/uninstall/sync)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, provisioner: object, registry: object) -> None:
        self._provisioner = provisioner
        self._registry = registry

    # -- Block 2: Query actions -----------------------------------------------------
    def list(self, tool_filter: ToolFilter = FILTER_EMPTY) -> ExitCode:
        """Port of tools/skill/skill.py cmd_list."""
        argv = SkillArgs([str(tool_filter)] if tool_filter else [])
        return ExitCode(self._registry.list(argv))

    def check(self) -> ExitCode:
        """Port of tools/skill/skill.py cmd_check."""
        return ExitCode(self._registry.check())

    def show(self, query: SkillQuery = QUERY_EMPTY) -> ExitCode:
        """Port of tools/skill/skill.py cmd_show."""
        return ExitCode(self._registry.show(SkillArgs([str(query)] if query else [])))

    # -- Block 3: Mutation actions ----------------------------------------------------
    def install(self, args: SkillArgs) -> ExitCode:
        """Port of tools/skill/skill.py cmd_install."""
        return ExitCode(self._registry.install(args))

    def uninstall(self, args: SkillArgs) -> ExitCode:
        """Port of tools/skill/skill.py cmd_uninstall."""
        return ExitCode(self._registry.uninstall(args))

    def sync(self, args: SkillArgs) -> ExitCode:
        """'sync' = install all (alias semantics from tools/skill/skill.py)."""
        return ExitCode(self._registry.sync(args))

    # -- Block 4: Protocol dispatch ----------------------------------------------------
    def execute(
        self,
        op: str,
        skill: str | None = None,
        target: Path | None = None,
    ) -> ExitCode:
        """Dispatch one skill op to the provisioner or registry capability."""
        if op in {"provision", "prune", "remove", "audit"}:
            return ExitCode(self._provisioner.execute(op, skill, target))
        return ExitCode(self._registry.execute(op, skill, target))

__all__ = ['ExitCode', 'SkillArgs', 'SkillProvisionResult', 'SkillQuery', 'ToolFilter']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "SkillArgs": SkillArgs,
    "SkillProvisionResult": SkillProvisionResult,
    "SkillQuery": SkillQuery,
    "ToolFilter": ToolFilter,
}
