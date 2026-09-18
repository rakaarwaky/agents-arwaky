"""Skill-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations
from modules.skill.src.taxonomy_skill_vo import SkillProvisionResult


from abc import ABC, abstractmethod


class ISkillAggregate(ABC):
    """Aggregate over the skill manager surface verbs."""

    @abstractmethod
    def list_skills(self, tool_filter: str = "") -> int:
        """List tools and their skills; return exit code."""
        return None

    @abstractmethod
    def check_skills(self) -> int:
        """Audit per-tool skill coverage and pack loadability; return exit code."""
        return None

    @abstractmethod
    def install_skills(self, args: list[str]) -> int:
        """Parse *args* and provision skills (install/copy/get/add/sync)."""
        return None

    @abstractmethod
    def uninstall_skills(self, args: list[str]) -> int:
        """Parse *args* and remove provisioned skills (uninstall/unskill/remove/delete)."""
        return None

    @abstractmethod
    def show_skill(self, query: str) -> int:
        """Display a skill's SKILL.md; return exit code."""
        return None

    @abstractmethod
    def sync_skills(self, args: list[str]) -> int:
        """Provision all skills for all tools; return exit code."""
        return None

__all__ = ['SkillProvisionResult']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"SkillProvisionResult": SkillProvisionResult}
