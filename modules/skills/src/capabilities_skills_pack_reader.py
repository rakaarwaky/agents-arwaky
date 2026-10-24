"""Skills pack reader capability (AES capabilities layer).

``SkillsPackReader`` implements ``ISkillsReaderProtocol`` (content access).
The pack-walking helpers live in ``utility_skill_pack`` (shared kernel), so
this file depends on contracts and the shared taxonomy only — never on a
sibling capability.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import ISkillsReaderProtocol
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillContent,
    SkillQuery,
    SkillsRoot,
)
from modules.shared.src.taxonomy_skill_vo import (
    sanitize_skill_name,
)
from modules.shared.src.utility_skill_pack import (
    default_pack_root,
    iter_skill_mds,
    parse_skill_frontmatter,
    read_skill_md,
)

__all__ = ["SkillsPackReader"]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsPackReader(ISkillsReaderProtocol):
    """Reads one skill's ``SKILL.md`` content from the pack at *pack_root*."""

    def __init__(self, pack_root: Path | None = None) -> None:
        self._root = pack_root or default_pack_root()

    # ─── Block 2: Protocol Method Implementation ──────────────
    def show_skill(
        self, query: SkillQuery, root: SkillsRoot | None = None
    ) -> SkillContent | None:
        """Return the raw SKILL.md content for *query*, or None if missing.

        Matches the frontmatter ``name:`` field, the parent directory name,
        or a hyphen-free spelling of either (``fetch`` ↔ ``fetch-mcp``).
        """
        pack_root = Path(root) if root is not None else self._root
        wanted = sanitize_skill_name(query, query)
        wanted_plain = wanted.replace("-", "")
        records = [
            (parse_skill_frontmatter(md), md) for md in iter_skill_mds(pack_root)
        ]
        exact = [
            (name_, md)
            for (name_, _desc), md in records
            if wanted in (name_, md.parent.name)
            or wanted_plain
            in (name_.replace("-", ""), md.parent.name.replace("-", ""))
        ]
        if exact:
            raw = read_skill_md(exact[0][1])
            return SkillContent(raw) if raw is not None else None
        prefixed = [
            md
            for (name_, _desc), md in records
            if name_.startswith(wanted + "-")
            or md.parent.name.startswith(wanted + "-")
        ]
        if len(prefixed) == 1:
            raw = read_skill_md(prefixed[0])
            return SkillContent(raw) if raw is not None else None
        return None

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "SkillsPackReader()"
