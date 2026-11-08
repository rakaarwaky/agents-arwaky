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

Split-module note: the consumers of this walker (the skill-design
feature's lint / catalog / discover / move capabilities) live in
``app/modules/skills_design`` under ``shared.src.skills_design``.
The ``shared.src`` prefix means every taxonomy import resolves to
this shared tree, not to a per-feature copy.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator
from pathlib import Path

from shared.src.design.taxonomy_skills_constant import (
    ASSETS_MARKER_FILENAME,
    IGNORED_CATEGORY_DIRS,
    PACK_MARKER_FILENAME,
)
from shared.src.design.taxonomy_skills_entity import (
    CategorySummary,
    SkillEntry,
)
import shared.src.discovery.utility_skills_core as _core


__all__ = [
    "assets_container",
    "category_dirs",
    "category_summaries",
    "iter_files",
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
    """Yield category directories, skipping hidden/ignored names."""
    return _core.category_dirs(skills_root)


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
    """Parse YAML frontmatter from ``path``; returns {} when absent/broken."""
    return _core.parse_frontmatter(path)



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
    return _core.skill_entries(skills_root)


def category_summaries(
    entries: Iterable[SkillEntry], skills_root: Path
) -> list[CategorySummary]:
    """Per-category description state and skill counts."""
    return _core.category_summaries(entries, skills_root)

