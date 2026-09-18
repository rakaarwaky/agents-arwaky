"""Skill-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.skill.taxonomy_skill_vo import SkillProvisionResult


class ISkillProvisioner(ABC):
    """Capability contract for skill pack provisioning (delegates to the
    shared skill_pack domain)."""

    @abstractmethod
    def install(self, tool_id: str, target_dir: Path, custom_dest: str = "", force: bool = False, link: bool = False, prune: bool = False) -> SkillProvisionResult:
        """Provision skills into a project workspace."""
        raise NotImplementedError

    @abstractmethod
    def prune(self, target_dir: Path, custom_dest: str = "") -> SkillProvisionResult:
        """Remove provisioned skill copies the pack no longer provides."""
        raise NotImplementedError

    @abstractmethod
    def audit(self) -> list[str]:
        """Return pack loadability finding strings; empty means clean."""
        raise NotImplementedError
