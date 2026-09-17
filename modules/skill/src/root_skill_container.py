"""Skill composition root — wires the registry + provisioner into the orchestrator."""
from __future__ import annotations

from modules.shared.src.skill.contract_skill_aggregate import ISkillAggregate
from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
from modules.skill.src.capabilities_skill_registry import SkillRegistry


class SkillContainer:
    """Construct the skill registry and pack provisioner, then the orchestrator."""

    def __init__(self) -> None:
        registry = SkillRegistry()
        provisioner = SkillPackProvisioner()
        self._orchestrator = SkillOrchestrator(registry, provisioner)

    @property
    def aggregate(self) -> ISkillAggregate:
        return self._orchestrator


def create_skill_feature() -> ISkillAggregate:
    """Fully-wired skill feature aggregate."""
    return SkillContainer().aggregate
