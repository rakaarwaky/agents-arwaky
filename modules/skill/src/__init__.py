"""Skill feature — public symbols.

Re-exports the orchestrator, capabilities, and surface entry points so
feature consumers can import from ``modules.skill`` directly. The
composition root (``root_skill_container``) is imported by callers
directly, not re-exported here, to keep the package free of a root
re-export cycle (AES205).
"""
from __future__ import annotations

from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
from modules.skill.src.surface_skill_command import main as cmd_skill

__all__ = [
    "SkillOrchestrator",
    "SkillPackProvisioner",
    "cmd_skill",
]
