"""Skills contract protocol (AES contract layer, ABC trait).

Two seam protocols so the skills agent coordinates two subsystems: the pack
index (list) and the pack reader (show). Capabilities implement these; the
composition root injects them into the agent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillContent,
    SkillQuery,
    SkillRecord,
)


class ISkillsIndexProtocol(ABC):
    """Read-only listing of the skill pack."""

    @abstractmethod
    def list_skills(self) -> Sequence[SkillRecord]:
        """Return one record per skill, sorted by name."""
        ...


class ISkillsReaderProtocol(ABC):
    """Read-only content access to one skill's SKILL.md."""

    @abstractmethod
    def show_skill(self, query: SkillQuery) -> SkillContent | None:
        """Return the raw SKILL.md content for *query*, or None if missing."""
        ...


__all__ = ["ISkillsIndexProtocol", "ISkillsReaderProtocol"]
