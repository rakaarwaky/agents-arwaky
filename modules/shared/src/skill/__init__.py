"""Shared skill-domain: taxonomy + contracts for skill provisioning."""
from modules.shared.src.skill.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.skill.contract_skill_protocol import ISkillProvisioner
from modules.shared.src.skill.taxonomy_skill_vo import SkillInfo, SkillProvisionResult

__all__ = [
    "ISkillAggregate",
    "ISkillProvisioner",
    "SkillInfo",
    "SkillProvisionResult",
]
