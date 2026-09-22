"""Skill-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_skill_vo import (
    ExitCode,
    SkillArgs,
    SkillDest,
    SkillProvisionResult,
    ToolFilter,
)


class ISkillProvisioner(ABC):
    """Capability contract for skill pack provisioning (delegates to the
    shared skill_pack domain)."""

    @abstractmethod
    def install(self, tool_id: ToolFilter, target_dir: Path, custom_dest: SkillDest = SkillDest(""), force: bool = False, link: bool = False, prune: bool = False) -> SkillProvisionResult:
        """Provision skills into a project workspace."""
        return None

    @abstractmethod
    def prune(self, target_dir: Path, custom_dest: SkillDest = SkillDest("")) -> SkillProvisionResult:
        """Remove provisioned skill copies the pack no longer provides."""
        return None

    @abstractmethod
    def audit(self) -> list[str]:
        """Return pack loadability finding strings; empty means clean."""
        return None


class ISkillRegistry(ABC):
    """Contract for the skill registry verb dispatch (injected by root)."""

    @abstractmethod
    def cmd_list(self, argv: SkillArgs) -> ExitCode:
        """List installed skills."""
        return None

    @abstractmethod
    def cmd_check(self) -> ExitCode:
        """Audit pack loadability."""
        return None

    @abstractmethod
    def cmd_show(self, argv: SkillArgs) -> ExitCode:
        """Show a single skill's content."""
        return None

    @abstractmethod
    def cmd_install(self, argv: SkillArgs) -> ExitCode:
        """Install a skill into a project."""
        return None

    @abstractmethod
    def cmd_uninstall(self, argv: SkillArgs) -> ExitCode:
        """Remove a provisioned skill."""
        return None

__all__ = ['ExitCode', 'ISkillProvisioner', 'ISkillRegistry', 'SkillArgs', 'SkillDest', 'SkillProvisionResult', 'ToolFilter']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "ISkillProvisioner": ISkillProvisioner,
    "ISkillRegistry": ISkillRegistry,
    "SkillArgs": SkillArgs,
    "SkillDest": SkillDest,
    "SkillProvisionResult": SkillProvisionResult,
    "ToolFilter": ToolFilter,
}
