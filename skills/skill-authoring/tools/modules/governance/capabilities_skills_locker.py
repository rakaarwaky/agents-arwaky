"""Skill locker capability (AES capabilities layer).

Toggles the locked flag on a skill's sidecar record.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.design.contract_skills_protocol import (
    ISkillsLockerProtocol,
)
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.maintenance.utility_lifecycle_support import (
    find_skill_dir,
    set_field,
)
from shared.src.storage.utility_skill_pack import default_pack_root

__all__ = ["SkillsLocker"]


# ─── Block 1: Module Declaration ──────────────
class SkillsLocker(ISkillsLockerProtocol):
    """Locker capability: lock/unlock verbs."""

# ─── Block 2: Module Contract ─────────────
    def lock(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            raise ValueError(f"No skill directory found for: {skill}")
        set_field(skill_dir, "locked", True)
        return {"skill": skill, "locked": True}

    def unlock(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            raise ValueError(f"No skill directory found for: {skill}")
        set_field(skill_dir, "locked", False)
        return {"skill": skill, "locked": False}
# ─── Block 3: Module Helpers ─────────
