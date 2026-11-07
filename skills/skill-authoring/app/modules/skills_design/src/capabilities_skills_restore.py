"""Skill restore capability (AES capabilities layer).

Moves a skill between the live pack and ``_archive/``: ``restore`` brings
an archived skill back, ``archive`` moves a live skill into the archive.
Both are the same domain (single-skill state transitions).
"""

from __future__ import annotations
from shared.src.skills_design.contract_skills_protocol import (
    ISkillsRestoreProtocol,
)


from pathlib import Path

from shared.src.skills_design.utility_skill_pack import default_pack_root
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot
from shared.src.skills_design.utility_lifecycle_support import (
    archive_skill,
    restore_skill,
)

__all__ = ["SkillsRestore"]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsRestore(ISkillsRestoreProtocol):
    """Restore capability: archive <-> active moves."""

    def __init__(self, reanchor=None) -> None:
        self._reanchor = reanchor

# ─── Block 2: Protocol Method Implementation ─────────────
    def archive(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        return archive_skill(skill, pack_root)

    def restore(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        reanchor = self._reanchor
        if reanchor is not None and not callable(reanchor):
            reanchor = None

# ─── Block 3: Dunder Methods, Factories & Helpers ─────────
        def _reanchor(skill_name: str, pack_root_path: Path) -> None:
            if callable(reanchor):
                reanchor(skill_name, SkillsRoot(pack_root_path))

        return restore_skill(skill, pack_root, _reanchor if reanchor else None)
