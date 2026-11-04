"""Skills lister capability (AES capabilities layer).

``SkillsLister`` implements ``ISkillsListerProtocol`` (listing).
The pack-walking helpers live in ``utility_skill_pack`` (shared kernel), so
this file depends on contracts and the shared taxonomy only — never on a
sibling capability.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from skills_design.src.utility_skill_pack import (
    default_pack_root,
    iter_skill_mds,
    parse_skill_frontmatter,
)
from skills_design.src.contract_skills_protocol import ISkillsListerProtocol
from skills_design.src.taxonomy_skills_vo import (
    SkillDescription,
    SkillRecord,
    SkillsJsonPayload,
    SkillsRoot,
)

__all__ = [
    "SkillsLister",
    "default_pack_root",
]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsLister(ISkillsListerProtocol):
    """Builds and serves the skill-pack listing rooted at *pack_root*."""

    def __init__(self, pack_root: Path | None = None) -> None:
        self._root = pack_root or default_pack_root()

    # ─── Block 2: Protocol Method Implementation ──────────────
    def list_skills(self, root: SkillsRoot | None = None) -> Sequence[SkillRecord]:
        """Return one record per skill in the pack, sorted by name."""
        pack_root = Path(root) if root is not None else self._root
        records: list[SkillRecord] = []
        for skill_md in iter_skill_mds(pack_root):
            name, description = parse_skill_frontmatter(skill_md)
            records.append(
                SkillRecord(
                    name=name,
                    description=SkillDescription(description),
                    path=skill_md,
                )
            )
        records.sort(key=lambda r: r.name)
        return records

    def list_skills_json(self, root: SkillsRoot | None = None) -> SkillsJsonPayload:
        """Return the global-skill JSON list: ``{"skills": [{name, source, path, loaded}]}``.

        Source is the repo pack only; the per-entry key order is pinned by
        ``contract_skills_index_json``.
        """
        records = self.list_skills(root)
        skills: list[dict] = []
        for record in records:
            skills.append(
                {
                    "name": record.name,
                    "source": str(self._root),
                    "path": str(record.path),
                    "loaded": True,
                }
            )
        return SkillsJsonPayload({"skills": skills})

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "SkillsLister()"
