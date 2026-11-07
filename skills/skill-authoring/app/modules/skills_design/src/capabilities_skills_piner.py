"""Skill piner capability (AES capabilities layer).

Toggles the pinned flag on a skill's sidecar record.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.utility_skill_pack import default_pack_root
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot
from shared.src.skills_design.utility_lifecycle_support import (
    find_skill_dir,
    set_field,
)

__all__ = ["SkillsPiner"]


class SkillsPiner:
    """Piner capability: pin/unpin verbs."""

    def pin(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            raise ValueError(f"No skill directory found for: {skill}")
        set_field(skill_dir, "pinned", True)
        return {"skill": skill, "pinned": True}

    def unpin(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            raise ValueError(f"No skill directory found for: {skill}")
        set_field(skill_dir, "pinned", False)
        return {"skill": skill, "pinned": False}
