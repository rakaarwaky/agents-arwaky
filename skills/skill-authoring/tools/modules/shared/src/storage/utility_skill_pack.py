"""Skill-pack filesystem helpers (AES utility layer).

Stateless readers over the skill pack: locating ``SKILL.md`` files, parsing
frontmatter, and reading body text. Shared by the two skills capabilities
(``SkillsLister`` and ``SkillsPackReader``) so neither imports the other.
"""
from __future__ import annotations

import posixpath
import re
from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    IGNORED_CATEGORY_DIRS,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)

__all__ = [
    "default_pack_root",
    "is_valid_skill_name",
    "iter_skill_mds",
    "parse_skill_frontmatter",
    "read_skill_md",
    "sanitize_skill_name",
]


def default_pack_root() -> Path:
    """Return the repo's ``skills/`` pack (the SSOT for all skills)."""
    return Path(__file__).resolve().parents[7]


def parse_skill_frontmatter(skill_md: Path) -> tuple[str, str]:
    """Return ``(name, description)`` from a SKILL.md, falling back to the dir."""
    fallback_name = skill_md.parent.name
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return (fallback_name, "")

    m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    name = fallback_name
    description = ""
    if m:
        fm = m.group(1)
        nm = re.search(r'^name:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
        if nm:
            name = nm.group(1).strip()
        desc = re.search(r'^description:\s*(.+)$', fm, re.MULTILINE)
        if desc:
            description = desc.group(1).strip().strip("\"'")
    return (name, description)


def iter_skill_mds(pack_root: Path) -> list[Path]:
    """Return each ``SKILL.md`` in the pack as a sorted list, by path.

    Category discovery walks the skills root directly: symlinked, hidden,
    and ignored category directories are skipped, so the read walker and
    the authoring walker see the same skill pack even though the glob would
    follow a symlinked category into a submodule.
    """
    if not pack_root.is_dir():
        return []
    found: list[Path] = []
    for category in sorted(pack_root.iterdir()):
        if not category.is_dir() or category.is_symlink():
            continue
        if category.name.startswith("."):
            continue
        if category.name in IGNORED_CATEGORY_DIRS:
            continue
        found.extend(sorted(category.glob("*/SKILL.md")))
    return sorted(found)


def read_skill_md(skill_md: Path) -> str | None:
    """Read a SKILL.md, returning None when it cannot be read."""
    try:
        return skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

def is_valid_skill_name(name: str) -> bool:
    """The name-format predicate for skill directory names.

    ``NAME_RE`` match AND no double hyphen AND 2-64 chars.
    """
    return bool(NAME_RE.match(name)) and "--" not in name and NAME_MIN <= len(name) <= NAME_MAX

def extract_skill_name(skill_md: Path) -> str:
    """Extract ``name:`` from SKILL.md frontmatter; fallback to parent dir name."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if m:
            nm = re.search(r"^name:\s*[\"']?(.+?)[\"']?\s*$", m.group(1), re.MULTILINE)
            if nm:
                return nm.group(1).strip()
    except OSError:
        pass
    return skill_md.parent.name

def sanitize_skill_name(raw: str, fallback: str) -> str:
    """Convert frontmatter name into a safe directory name (prevents path traversal)."""
    raw = (raw or "").strip().replace("\\", "/")
    raw = posixpath.basename(raw)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    if not name:
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", fallback).strip(".-") or "skill"
    return name[:64]
