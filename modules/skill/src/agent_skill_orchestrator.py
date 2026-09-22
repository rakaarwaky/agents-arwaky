"""Skill agent orchestrator — coordinates registry + pack provisioner.

Dispatches every surface verb to the original command handlers, ported
verbatim from tools/skill/skill.py into
:mod:`modules.skill.src.capabilities_skill_registry` (injected as
ISkillRegistry by the root composition layer).
"""
from __future__ import annotations
from modules.shared.src.taxonomy_skill_vo import (
    ExitCode,
    SkillArgs,
    SkillProvisionResult,
    SkillQuery,
    ToolFilter,
)

from modules.shared.src.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.contract_skill_protocol import ISkillProvisioner, ISkillRegistry


class SkillOrchestrator(ISkillAggregate):
    """Routing of skill surface verbs to the capabilities (original bodies).

    # Block 1: Constructor
    # Block 2: Query verbs (list/check/show)
    # Block 3: Mutation verbs (install/uninstall/sync)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, provisioner: ISkillProvisioner, registry: ISkillRegistry) -> None:
        self._provisioner = provisioner
        self._registry = registry

    # -- Block 2: Query verbs -----------------------------------------------------
    def list_skills(self, tool_filter: ToolFilter = ToolFilter("")) -> ExitCode:
        """Port of tools/skill/skill.py cmd_list."""
        argv = SkillArgs([str(tool_filter)] if tool_filter else [])
        return ExitCode(self._registry.cmd_list(argv))

    def check_skills(self) -> ExitCode:
        """Port of tools/skill/skill.py cmd_check."""
        return ExitCode(self._registry.cmd_check())

    def show_skill(self, query: SkillQuery = SkillQuery("")) -> ExitCode:
        """Port of tools/skill/skill.py cmd_show."""
        return ExitCode(self._registry.cmd_show(SkillArgs([str(query)] if query else [])))

    # -- Block 3: Mutation verbs ----------------------------------------------------
    def install_skills(self, args: SkillArgs) -> ExitCode:
        """Port of tools/skill/skill.py cmd_install."""
        return ExitCode(self._registry.cmd_install(args))

    def uninstall_skills(self, args: SkillArgs) -> ExitCode:
        """Port of tools/skill/skill.py cmd_uninstall."""
        return ExitCode(self._registry.cmd_uninstall(args))

    def sync_skills(self, args: SkillArgs) -> ExitCode:
        """'sync' = install all (alias semantics from tools/skill/skill.py)."""
        return ExitCode(self._registry.cmd_install(SkillArgs(["all", *list(args)])))

__all__ = ['ExitCode', 'SkillArgs', 'SkillProvisionResult', 'SkillQuery', 'ToolFilter']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "SkillArgs": SkillArgs,
    "SkillProvisionResult": SkillProvisionResult,
    "SkillQuery": SkillQuery,
    "ToolFilter": ToolFilter,
}
