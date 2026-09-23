"""Skill-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_skill_vo import (
    ExitCode,
    SkillArgs,
    SkillProvisionResult,
    SkillQuery,
    ToolFilter,
)


class ISkillAggregate(ABC):
    """Aggregate over the skill manager surface actions."""

    @abstractmethod
    def list_skills(self, tool_filter: ToolFilter = ToolFilter("")) -> ExitCode:
        """List tools and their skills; return exit code."""
        ...
    @abstractmethod
    def check_skills(self) -> ExitCode:
        """Audit per-tool skill coverage and pack loadability; return exit code."""
        ...
    @abstractmethod
    def install_skills(self, args: SkillArgs) -> ExitCode:
        """Parse *args* and provision skills (install/copy/get/add/sync)."""
        ...
    @abstractmethod
    def uninstall_skills(self, args: SkillArgs) -> ExitCode:
        """Parse *args* and remove provisioned skills (uninstall/unskill/remove/delete)."""
        ...
    @abstractmethod
    def show_skill(self, query: SkillQuery = SkillQuery("")) -> ExitCode:
        """Display a skill's SKILL.md; return exit code."""
        ...
    @abstractmethod
    def sync_skills(self, args: SkillArgs) -> ExitCode:
        """Provision all skills for all tools; return exit code."""
        ...

__all__ = ['ExitCode', 'ISkillAggregate', 'SkillArgs', 'SkillProvisionResult', 'SkillQuery', 'ToolFilter']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "ISkillAggregate": ISkillAggregate,
    "SkillArgs": SkillArgs,
    "SkillProvisionResult": SkillProvisionResult,
    "SkillQuery": SkillQuery,
    "ToolFilter": ToolFilter,
}
