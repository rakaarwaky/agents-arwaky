"""Skill agent orchestrator — coordinates registry + pack provisioner.

Dispatches every surface verb to the original command handlers, ported
verbatim from tools/skill/skill.py into
:mod:`modules.skill.src.capabilities_skill_registry`.
"""
from __future__ import annotations

from modules.skill.contract.contract_skill_aggregate import ISkillAggregate
from modules.skill.contract.contract_skill_protocol import ISkillProvisioner

from modules.skill.src import capabilities_skill_registry as _reg


class SkillOrchestrator(ISkillAggregate):
    """Routing of skill surface verbs to the capabilities (original bodies).

    # Block 1: Constructor
    # Block 2: Query verbs (list/check/show)
    # Block 3: Mutation verbs (install/uninstall/sync)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, provisioner: ISkillProvisioner) -> None:
        self._provisioner = provisioner

    # -- Block 2: Query verbs -----------------------------------------------------
    def list_skills(self, tool_filter: str = "") -> int:
        """Port of tools/skill/skill.py cmd_list."""
        argv = [tool_filter] if tool_filter else []
        return _reg.cmd_list(argv)

    def check_skills(self) -> int:
        """Port of tools/skill/skill.py cmd_check."""
        return _reg.cmd_check()

    def show_skill(self, query: str) -> int:
        """Port of tools/skill/skill.py cmd_show."""
        return _reg.cmd_show([query] if query else [])

    # -- Block 3: Mutation verbs ----------------------------------------------------
    def install_skills(self, args: list[str]) -> int:
        """Port of tools/skill/skill.py cmd_install."""
        return _reg.cmd_install(args)

    def uninstall_skills(self, args: list[str]) -> int:
        """Port of tools/skill/skill.py cmd_uninstall."""
        return _reg.cmd_uninstall(args)

    def sync_skills(self, args: list[str]) -> int:
        """'sync' = install all (alias semantics from tools/skill/skill.py)."""
        return _reg.cmd_install(["all", *args])
