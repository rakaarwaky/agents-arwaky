"""Skills capabilities (AES capabilities layer).

Two capabilities, one per contract seam:
- ``SkillsIndexBuilder`` implements ``ISkillsIndexProtocol`` (listing)
- ``SkillsPackReader`` implements ``ISkillsReaderProtocol`` (content access)

Both are read-only and walk the skill pack at ``skills/`` (the SSOT).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import ISkillsIndexProtocol
from modules.shared.src.skills.taxonomy_skills_vo import (
    SkillDescription,
    SkillRecord,
)
from modules.shared.src.taxonomy_skill_vo import (
    extract_skill_name,
)

__all__ = [
    "SkillsIndexBuilder",
    "default_pack_root",
]


def default_pack_root() -> Path:
    """Return the repo's ``skills/`` pack (the SSOT for all skills)."""
    return Path(__file__).resolve().parents[3] / "skills"


def _parse_frontmatter(skill_md: Path) -> tuple[str, str]:
    """Return ``(name, description)`` from a SKILL.md, falling back to the dir."""
    fallback_name = skill_md.parent.name
    name = extract_skill_name(skill_md)
    description = ""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return (name or fallback_name, description)
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            for line in text[4:end].splitlines():
                if line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip("\"'")
    return (name, description)


def _iter_skill_mds(pack_root: Path) -> list[Path]:
    """Yield each ``SKILL.md`` in the pack, sorted by path."""
    if not pack_root.is_dir():
        return []
    return sorted(pack_root.glob("*/*/SKILL.md"))


def _read_skill_md(skill_md: Path) -> str | None:
    """Read a SKILL.md, returning None when it cannot be read."""
    try:
        return skill_md.read_text(encoding="utf-8")
    except OSError:
        return None


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsIndexBuilder(ISkillsIndexProtocol):
    """Builds and serves the skill-pack index rooted at *pack_root*."""

    def __init__(self, pack_root: Path | None = None) -> None:
        self._root = pack_root or default_pack_root()

    # ─── Block 2: Protocol Method Implementation ──────────────
    def list_skills(self) -> Sequence[SkillRecord]:
        """Return one record per skill in the pack, sorted by name."""
        records: list[SkillRecord] = []
        for skill_md in _iter_skill_mds(self._root):
            name, description = _parse_frontmatter(skill_md)
            records.append(
                SkillRecord(
                    name=name,
                    description=SkillDescription(description),
                    path=skill_md,
                )
            )
        records.sort(key=lambda r: r.name)
        return records

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────


