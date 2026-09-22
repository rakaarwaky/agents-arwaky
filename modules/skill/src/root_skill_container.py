"""Skill composition root — wires the pack provisioner into the orchestrator."""
from __future__ import annotations

from modules.shared.src.contract_skill_aggregate import ISkillAggregate
from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
from modules.skill.src.surface_skill_command import SkillRegistryAdapter


class SkillContainer:
    """Construct the skill pack provisioner + registry, then the orchestrator."""

    def __init__(self) -> None:
        provisioner = SkillPackProvisioner()
        registry = SkillRegistryAdapter()
        self._orchestrator = SkillOrchestrator(provisioner, registry)

    @property
    def aggregate(self) -> ISkillAggregate:
        return self._orchestrator


def create_skill_feature() -> ISkillAggregate:
    """Fully-wired skill feature aggregate."""
    return SkillContainer().aggregate
