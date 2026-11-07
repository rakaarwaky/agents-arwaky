"""Skill restore capability (AES capabilities layer).

Moves an archived skill back into the live pack.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.utility_skill_pack import default_pack_root
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot

from skills_design.src.skills_lifecycle_core import restore_skill

__all__ = ["SkillsRestore"]


class SkillsRestore:
    """Restore capability: archive -> active move."""

    def __init__(self, reanchor=None) -> None:
        self._reanchor = reanchor

    def restore(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        reanchor = self._reanchor
        if reanchor is not None and not callable(reanchor):
            reanchor = None

        def _reanchor(skill_name: str, pack_root_path: Path) -> None:
            if callable(reanchor):
                reanchor(skill_name, SkillsRoot(pack_root_path))

        return restore_skill(skill, pack_root, _reanchor if reanchor else None)
