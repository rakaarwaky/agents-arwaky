"""Skill-pack filesystem helpers (AES utility layer).

Stateless readers over the skill pack: locating ``SKILL.md`` files, parsing
frontmatter, and reading body text. Shared by the two skills capabilities
(``SkillsIndexBuilder`` and ``SkillsPackReader``) so neither imports the
other.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.common.taxonomy_skill_vo import (
    extract_skill_name,
)
from modules.shared.src.common.utility_skills_tree import category_dirs

__all__ = [
    "default_pack_root",
    "iter_skill_mds",
    "parse_skill_frontmatter",
    "read_skill_md",
]


def default_pack_root() -> Path:
    """Return the repo's ``skills/`` pack (the SSOT for all skills)."""
    return Path(__file__).resolve().parents[4] / "skills"


def parse_skill_frontmatter(skill_md: Path) -> tuple[str, str]:
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


def iter_skill_mds(pack_root: Path) -> list[Path]:
    """Yield each ``SKILL.md`` in the pack, sorted by path.

    Category discovery delegates to ``category_dirs`` (design S6): symlinked,
    hidden, and ignored category directories are skipped, so the read walker
    and the authoring walker see the same skill pack even though the glob
    would follow a symlinked category into a submodule.
    """
    if not pack_root.is_dir():
        return []
    return sorted(
        skill_md
        for category in category_dirs(pack_root)
        for skill_md in category.glob("*/SKILL.md")
    )


def read_skill_md(skill_md: Path) -> str | None:
    """Read a SKILL.md, returning None when it cannot be read."""
    try:
        return skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
