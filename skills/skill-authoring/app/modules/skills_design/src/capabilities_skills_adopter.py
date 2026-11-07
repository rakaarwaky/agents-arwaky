"""Skill adopter capability (AES capabilities layer).

Marks a skill as agent-managed by setting ``created_by="agent"``.
"""

from __future__ import annotations
from shared.src.skills_design.contract_skills_protocol import (
    ISkillsAdopterProtocol,
)


from pathlib import Path

from shared.src.skills_design.utility_skill_pack import default_pack_root
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot
from shared.src.skills_design.utility_lifecycle_support import (
    find_skill_dir,
    set_field,
)

__all__ = ["SkillsAdopter"]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsAdopter(ISkillsAdopterProtocol):
    """Adopter capability: adopt verb."""

# ─── Block 2: Protocol Method Implementation ─────────────
    def adopt(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            raise ValueError(f"No skill directory found for: {skill}")
        set_field(skill_dir, "created_by", "agent")
        return {"skill": skill, "created_by": "agent"}
# ─── Block 3: Dunder Methods, Factories & Helpers ─────────
