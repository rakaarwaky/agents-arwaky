"""Skill-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ISkillAggregate(ABC):
    """Aggregate over the skill manager surface verbs."""

    @abstractmethod
    def list_skills(self, tool_filter: str = "") -> int:
        """List tools and their skills; return exit code."""
        raise NotImplementedError

    @abstractmethod
    def check_skills(self) -> int:
        """Audit per-tool skill coverage and pack loadability; return exit code."""
        raise NotImplementedError

    @abstractmethod
    def install_skills(self, args: list[str]) -> int:
        """Parse *args* and provision skills (install/copy/get/add/sync)."""
        raise NotImplementedError

    @abstractmethod
    def uninstall_skills(self, args: list[str]) -> int:
        """Parse *args* and remove provisioned skills (uninstall/unskill/remove/delete)."""
        raise NotImplementedError

    @abstractmethod
    def show_skill(self, query: str) -> int:
        """Display a skill's SKILL.md; return exit code."""
        raise NotImplementedError

    @abstractmethod
    def sync_skills(self, args: list[str]) -> int:
        """Provision all skills for all tools; return exit code."""
        raise NotImplementedError
