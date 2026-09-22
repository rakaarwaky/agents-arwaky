"""Skill-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_skill_vo import SkillProvisionResult


class ISkillProvisioner(ABC):
    """Capability contract for skill pack provisioning (delegates to the
    shared skill_pack domain)."""

    @abstractmethod
    def install(self, tool_id: str, target_dir: Path, custom_dest: str = "", force: bool = False, link: bool = False, prune: bool = False) -> SkillProvisionResult:
        """Provision skills into a project workspace."""
        return None

    @abstractmethod
    def prune(self, target_dir: Path, custom_dest: str = "") -> SkillProvisionResult:
        """Remove provisioned skill copies the pack no longer provides."""
        return None

    @abstractmethod
    def audit(self) -> list[str]:
        """Return pack loadability finding strings; empty means clean."""
        return None


class ISkillRegistry(ABC):
    """Contract for the skill registry verb dispatch (injected by root)."""

    @abstractmethod
    def cmd_list(self, argv: list[str]) -> int:
        """List installed skills."""
        return None

    @abstractmethod
    def cmd_check(self) -> int:
        """Audit pack loadability."""
        return None

    @abstractmethod
    def cmd_show(self, argv: list[str]) -> int:
        """Show a single skill's content."""
        return None

    @abstractmethod
    def cmd_install(self, argv: list[str]) -> int:
        """Install a skill into a project."""
        return None

    @abstractmethod
    def cmd_uninstall(self, argv: list[str]) -> int:
        """Remove a provisioned skill."""
        return None
