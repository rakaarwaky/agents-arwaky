"""Skill-tree walking and frontmatter parsing (AES utility layer).

Stateless technical readers over a skills root: category discovery,
the two-level loaders' walk, and frontmatter parsing. Business
decisions (which issue each shape raises) live in the validator
capability; this module only reports what is on disk.

This module is self-contained — it imports only from the taxonomy
layer (``shared.src.design``) and the governance error module, never
from a sibling utility file. The ``relpath`` helper lives here
directly (single consumer: the capability layer).

Optional PyYAML: load-bearing only when present; the single-line
fallback keeps the pack readable on a host without it.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path
from types import ModuleType

from shared.src.common.taxonomy_common_constant import (
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
)
from shared.src.common.taxonomy_common_entity import (
    CategorySummary,
    SkillEntry,
)
from shared.src.common.taxonomy_common_error import SkillsRootError

_yaml_mod: ModuleType | None
try:
    import yaml as _yaml_mod
except ImportError:  # pragma: no cover - exercised by the S8 test
    _yaml_mod = None

__all__ = [
    "category_dirs",
    "category_summaries",
    "clean_one_line",
    "parse_frontmatter",
    "relpath",
    "skill_entries",
]


def relpath(path: Path, skills_root: Path) -> str:
    """A skills-root-relative path when possible, else the absolute one."""
    try:
        return str(path.relative_to(skills_root))
    except ValueError:
        return str(path)


def clean_one_line(value: object) -> str:
    """Collapse whitespace to single spaces and strip the edges."""
    return " ".join(str(value).split()).strip()


def category_dirs(skills_root: Path) -> Iterator[Path]:
    """Yield category directories, skipping hidden/ignored names.

    Raises ``SkillsRootError`` when the root is missing or is not a
    directory: a capability must not terminate the process, so the
    legacy ``SystemExit(1)`` becomes the typed usage error (exit 2).
    """
    if not skills_root.is_dir():
        raise SkillsRootError(f"Skills root does not exist: {skills_root}")

    for path in sorted(skills_root.iterdir()):
        if path.is_symlink() or not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if path.name in IGNORED_CATEGORY_DIRS:
            continue
        yield path


def parse_frontmatter(path: Path) -> dict[str, object]:
    """Parse YAML frontmatter from ``path``; returns {} when absent/broken.

    Optional PyYAML pass, then a minimal single-line ``key: value``
    fallback. The fallback is load-bearing: CI installs ``pyyaml`` but
    ``pyproject.toml`` declares no dependencies, so a host without it
    must still parse the pack.
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

    if _yaml_mod is not None:
        try:
            parsed = _yaml_mod.safe_load(fm_text)
        except _yaml_mod.YAMLError:  # degraded to the fallback parser below
            parsed = None
    else:
        parsed = None

    if isinstance(parsed, dict):
        return parsed

    data: dict[str, object] = {}
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

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        data[key] = value

    return data


def skill_entries(skills_root: Path) -> list[SkillEntry]:
    """All discoverable skills: ``category/*/SKILL.md`` with frontmatter."""
    entries: list[SkillEntry] = []

    for category in category_dirs(skills_root):
        for skill_md in sorted(category.glob("*/SKILL.md")):
            skill_dir = skill_md.parent
            frontmatter = parse_frontmatter(skill_md)

            entries.append(
                SkillEntry(
                    skill=skill_dir.name,
                    frontmatter_name=clean_one_line(
                        frontmatter.get("name", skill_dir.name)
                    ),
                    category=category.name,
                    description=clean_one_line(frontmatter.get("description", "")),
                    when_to_use=clean_one_line(frontmatter.get("when-to-use", "")),
                    path=f"{category.name}/{skill_dir.name}",
                )
            )

    return entries


def category_summaries(
    entries: Iterable[SkillEntry], skills_root: Path
) -> list[CategorySummary]:
    """Per-category description state and skill counts.

    ``entries`` is materialized once because it is re-iterated per
    category; a generator passed here would be consumed by the first
    category and silently zero every later category's count.
    """
    entries = list(entries)
    summaries: list[CategorySummary] = []

    for category in category_dirs(skills_root):
        desc_file = category / CATEGORY_DESCRIPTION_FILENAME
        description = ""
        exists = desc_file.exists()

        if exists:
            frontmatter = parse_frontmatter(desc_file)
            description = clean_one_line(frontmatter.get("description", ""))

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
