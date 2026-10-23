"""Data model and tree walking for the skill library.

Lifted verbatim from ``skill-librarian/scripts/librarian.py``: the
frontmatter parser and the tree walk, adapted to take an explicit
``skills_root`` so fixtures and tests can
point at crafted trees. ``librarian.py`` passes its own ``SKILLS_ROOT``
and keeps byte-identical behavior.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

try:
    import yaml
except ImportError:
    yaml = None

# This file lives in <pack>/scripts/; _rules/ sits next to it.
_RULES_DIR = Path(__file__).resolve().parent.parent / "_rules"
if str(_RULES_DIR) not in sys.path:
    sys.path.insert(0, str(_RULES_DIR))

from skill_rules import (
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
    clean_one_line,
)

__all__ = [
    "ASSETS_MARKER_FILENAME",
    "PACK_MARKER_FILENAME",
    "CategorySummary",
    "Issue",
    "SkillEntry",
    "assets_container",
    "category_dirs",
    "category_summaries",
    "parse_frontmatter",
    "skill_entries",
    "too_deep_exempt_paths",
]


# ── DM1 / DM2 markers ────────────────────────────────────────────────

#: The DM2 asset-container marker file. A category directory that carries
#: it (with frontmatter ``kind: assets``) declares itself a cross-skill
#: asset container, not a category of skills: ``validate`` and the weed
#: report skip its ``empty-category`` / ``missing-category-description``
#: checks (design §6.3 DM2). Declared file, not a directory-name
#: heuristic — a real category can never opt out accidentally (R8).
ASSETS_MARKER_FILENAME: Final = "ASSETS.md"

#: The DM1 nested-pack marker file. A subdirectory of a category that
#: holds its own ``SKILL.md`` files one level deeper than the loader's
#: two-level walk declares itself a nested pack by carrying this marker:
#: ``validate`` skips the ``too-deep`` error for those files (design §6.3
#: DM1). Opt-in only — without the marker, depth violations are
#: unchanged (R6). The marker affects ``validate``'s depth check only;
#: ``skill_entries`` / the catalog / ``discover`` do not descend into it.
PACK_MARKER_FILENAME: Final = "pack.toml"


def assets_container(skills_root: Path) -> set[str]:
    """Category names that carry a declared DM2 asset-container marker.
    """
    declared = set()
    for category in category_dirs(skills_root):
        marker = category / ASSETS_MARKER_FILENAME
        if not marker.is_file():
            continue
        fm = parse_frontmatter(marker)
        if fm.get("kind") == "assets":
            declared.add(category.name)
    return declared


def too_deep_exempt_paths(skills_root: Path) -> set[str]:
    """DM1 nested-pack exemption: the ``category/pack/SKILL.md`` paths
    whose intermediate directory carries the ``pack.toml`` marker.
    """
    exempt = set()
    for category in category_dirs(skills_root):
        for skill_md in category.glob("*/*/SKILL.md"):
            marker = skill_md.parent.parent / PACK_MARKER_FILENAME
            if marker.is_file():
                try:
                    exempt.add(str(skill_md.relative_to(skills_root)))
                except ValueError:
                    continue
    return exempt


def parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from ``path``; returns {} when absent/broken.

    Verbatim from ``librarian.py``: optional PyYAML pass, then a minimal
    single-line ``key: value`` fallback.
    """
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}

    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}

    parts = stripped.split("---", 2)
    if len(parts) < 3:
        return {}

    fm_text = parts[1]

    if yaml is not None:
        try:
            data = yaml.safe_load(fm_text)
            if isinstance(data, dict):
                return data
        except Exception:  # noqa: BLE001,S110  (degrade to fallback parser)
            pass

    data = {}
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        if line != line.lstrip():
            continue
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if not key or value in {"", "|", ">", "|-", ">-"}:
            continue
        if value.startswith(("[", "{", "- ")):
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
            value = value[1:-1]

        data[key] = value

    return data


@dataclass(frozen=True)
class SkillEntry:
    """One discoverable skill at ``category/skill``.

    Fields mirror the dict the original ``skill_entries`` produced, so
    callers can index them identically.
    """

    skill: str
    frontmatter_name: str
    category: str
    description: str
    path: str


@dataclass(frozen=True)
class CategorySummary:
    """One category folder: description state and skill count."""

    category: str
    description: str
    description_file_exists: bool
    skill_count: int


@dataclass(frozen=True)
class Issue:
    """One validation issue.

    ``locator`` is the ``path`` or ``category`` string the report prints
    after the issue type (or ``None`` for library-wide issues); ``message``
    must be the verbatim string from ``skill_rules.ISSUE_MESSAGES``.
    """

    type: str
    message: str
    locator: str | None = None


def category_dirs(skills_root: Path) -> Iterator[Path]:
    """Yield category directories, skipping hidden/ignored names.

    Raises ``SystemExit(1)`` when the root is missing; the missing-root
    error line is printed by the caller (``fail`` in ``librarian.py``,
    which stays byte-identical to the original stderr output).
    """
    if not skills_root.is_dir():
        raise SystemExit(1)

    for path in sorted(skills_root.iterdir()):
        if not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if path.name in IGNORED_CATEGORY_DIRS:
            continue
        yield path


def skill_entries(skills_root: Path) -> list[SkillEntry]:
    """All discoverable skills: ``category/*/SKILL.md`` with frontmatter."""
    entries = []

    for category in category_dirs(skills_root):
        for skill_md in sorted(category.glob("*/SKILL.md")):
            skill_dir = skill_md.parent
            fm = parse_frontmatter(skill_md)

            entries.append(
                SkillEntry(
                    skill=skill_dir.name,
                    frontmatter_name=clean_one_line(fm.get("name", skill_dir.name)),
                    category=category.name,
                    description=clean_one_line(fm.get("description", "")),
                    path=f"{category.name}/{skill_dir.name}",
                )
            )

    return entries


def category_summaries(entries: Iterable[SkillEntry], skills_root: Path) -> list[CategorySummary]:
    """Per-category description state and skill counts."""
    summaries = []

    for category in category_dirs(skills_root):
        desc_file = category / CATEGORY_DESCRIPTION_FILENAME
        description = ""
        exists = desc_file.exists()

        if exists:
            fm = parse_frontmatter(desc_file)
            description = clean_one_line(fm.get("description", ""))

        skill_count = sum(1 for entry in entries if entry.category == category.name)

        summaries.append(
            CategorySummary(
                category=category.name,
                description=description,
                description_file_exists=exists,
                skill_count=skill_count,
            )
        )

    return summaries

