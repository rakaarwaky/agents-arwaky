"""Skill-tree walking and frontmatter parsing (AES utility layer).

Stateless technical readers over a skills root: category discovery, the
two-level loaders' walk, frontmatter parsing, the DM1/DM2 marker
exemptions, and non-following recursive file iteration. The business
decisions (which issue each shape raises) live in the validator
capability; this module only reports what is on disk.

Recursive scans use ``os.walk(followlinks=False)`` rather than
``Path.rglob`` so a symlinked directory is never descended and a
symlink loop cannot hang a scan (design S6; version-independent — CI
pins Python 3.12, where ``Path.rglob`` has no ``follow_symlinks``).
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator
from pathlib import Path
from types import ModuleType

from modules.shared.src.common.utility_skills_markdown import clean_one_line
from modules.shared.src.skills.taxonomy_skills_constant import (
    ASSETS_MARKER_FILENAME,
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
    PACK_MARKER_FILENAME,
)
from modules.shared.src.skills.taxonomy_skills_entity import (
    CategorySummary,
    SkillEntry,
)
from modules.shared.src.skills.taxonomy_skills_error import SkillsRootError

yaml: ModuleType | None = None
try:
    import yaml as _yaml
    yaml = _yaml
except ImportError:  # pragma: no cover - exercised by the S8 test
    yaml = None

__all__ = [
    "assets_container",
    "category_dirs",
    "category_summaries",
    "iter_files",
    "iter_markdown_files",
    "iter_relative_skill_mds",
    "parse_frontmatter",
    "relpath",
    "skill_entries",
    "too_deep_exempt_paths",
]


def relpath(path: Path, skills_root: Path) -> str:
    """A skills-root-relative path when possible, else the absolute one."""
    try:
        return str(path.relative_to(skills_root))
    except ValueError:
        return str(path)


def category_dirs(skills_root: Path) -> Iterator[Path]:
    """Yield category directories, skipping hidden/ignored names.

    Raises ``SkillsRootError`` when the root is missing or is not a
    directory: a capability must not terminate the process, so the
    legacy ``SystemExit(1)`` becomes the typed usage error (exit 2).
    """
    if not skills_root.is_dir():
        raise SkillsRootError(f"Skills root does not exist: {skills_root}")

    for path in sorted(skills_root.iterdir()):
        if not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if path.name in IGNORED_CATEGORY_DIRS:
            continue
        yield path


def iter_files(folder: Path) -> Iterator[Path]:
    """Yield every regular file under ``folder`` without following symlinks.

    Deterministic (sorted names per directory); symlinked directories are
    listed but never descended, so a loop cannot hang the scan.
    """
    if not folder.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
        dirnames.sort()
        for name in sorted(filenames):
            yield Path(dirpath) / name


def iter_markdown_files(skills_root: Path) -> Iterator[Path]:
    """Yield every ``*.md`` file under ``skills_root`` (no symlink descent)."""
    for path in iter_files(skills_root):
        if path.suffix == ".md":
            yield path


def iter_relative_skill_mds(skills_root: Path, depth: int) -> Iterator[Path]:
    """Yield ``SKILL.md`` files exactly ``depth`` directories below the root.

    ``depth=1`` is ``category/SKILL.md`` (invalid placement) and
    ``depth=3`` is ``category/pack/nested/SKILL.md`` (too deep). Hidden
    and ignored category directories are skipped, mirroring the legacy
    ``_iter_skill_md_files_relative``.
    """
    pattern = "/".join(["*"] * depth + ["SKILL.md"])
    for path in skills_root.glob(pattern):
        try:
            rel = path.relative_to(skills_root)
        except ValueError:
            continue
        parts = rel.parts
        if not parts:
            continue
        if parts[0].startswith("."):
            continue
        if parts[0] in IGNORED_CATEGORY_DIRS:
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

    if yaml is not None:
        try:
            parsed = yaml.safe_load(fm_text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:  # degraded to the fallback parser below
            pass

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


def assets_container(skills_root: Path) -> set[str]:
    """Category names that carry a declared DM2 asset-container marker."""
    declared = set()
    for category in category_dirs(skills_root):
        marker = category / ASSETS_MARKER_FILENAME
        if not marker.is_file():
            continue
        frontmatter = parse_frontmatter(marker)
        if frontmatter.get("kind") == "assets":
            declared.add(category.name)
    return declared


def too_deep_exempt_paths(skills_root: Path) -> set[str]:
    """DM1 nested-pack exemption: ``category/pack/SKILL.md`` paths whose
    intermediate directory carries the ``pack.toml`` marker."""
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


def skill_entries(skills_root: Path) -> list[SkillEntry]:
    """All discoverable skills: ``category/*/SKILL.md`` with frontmatter."""
    entries = []

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
    summaries = []

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
