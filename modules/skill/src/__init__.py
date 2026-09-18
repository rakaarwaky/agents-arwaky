"""Skill feature — public symbols.

Re-exports the orchestrator, container, and surface entry points so
feature consumers can import from ``modules.skill`` directly.
"""
from __future__ import annotations

from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
from modules.skill.src.root_skill_container import SkillContainer, create_skill_feature
from modules.cli.src.surface_skill_command import cmd_skill

__all__ = [
    "SkillContainer",
    "SkillOrchestrator",
    "SkillPackProvisioner",
    "cmd_skill",
    "create_skill_feature",
]
