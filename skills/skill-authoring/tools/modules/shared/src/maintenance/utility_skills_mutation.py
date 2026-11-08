"""Skills mutation utilities (AES utility layer).

Shared helpers for the mover, archiver, and creator capabilities:
skill-dir resolution, category-name validation, containment assertion,
and the weed / repair report generators. These were split out of the
retired ``capabilities_skills_mutator`` so each mutation capability can
depend on the shared kernel without a sibling import.

The skill-tree walkers and parsers this file needs live in
``utility_discovery_core`` -- the single documented AES201 exception.
AES201 forbids utility files importing one another; this module imports
from the core module (not from a sibling utility) so the dependency
graph stays acyclic.
"""
from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator
from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)
from shared.src.design.taxonomy_skills_constant import (
    ARCHIVE_DIRNAME,
    ASSETS_MARKER_FILENAME,
)
from shared.src.common.taxonomy_common_error import (
    CategoryNameError,
    SkillNotFoundError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.design.taxonomy_skills_vo import (
    MutationPlan,
    MutationStep,
)

import shared.src.discovery.utility_discovery_core as _tree

def _assets_container(skills_root: Path) -> set[str]:
    """Category names that carry a declared DM2 asset-container marker."""
    declared: set[str] = set()
    for category in _tree.category_dirs(skills_root):
        marker = category / ASSETS_MARKER_FILENAME
        if not marker.is_file():
            continue
        frontmatter = _tree.parse_frontmatter(marker)
        if frontmatter.get("kind") == "assets":
            declared.add(category.name)
    return declared


# ─── Inlined tree walkers (private; utility files stay independent, AES201) ──



def _yaml_quote(value: object) -> str:
    """Quote a YAML scalar the way the original ``librarian.py`` did."""
    return json.dumps(str(value), ensure_ascii=False)


def archive_root(skills_root: Path) -> Path:
    """The archive tree for a skills root."""
    return skills_root / ARCHIVE_DIRNAME


def assert_within_root(path: Path, root: Path) -> None:
    """Fail closed when a computed destination escapes the skills root."""
    try:
        contained = path.resolve().is_relative_to(root.resolve())
    except OSError:
        contained = False
    if not contained:
        raise SkillsUsageError(f"Refusing to write outside the skills root: {path}")


def write_category_description(
    category: Path, description: str, force: bool = False
) -> bool:
    """Write ``category/DESCRIPTION.md``; keep an existing one unless ``force``."""
    desc_file = category / CATEGORY_DESCRIPTION_FILENAME

    if desc_file.exists() and not force:
        return False

    desc_file.write_text(
        f"---\ndescription: {_yaml_quote(description)}\n---\n",
        encoding="utf-8",
    )
    return True


def name_mismatch_repairs(skills_root: Path) -> list[tuple[Path, str]]:
    """The ``(skill_md, expected_name)`` pairs a repair would rewrite."""
    pairs: list[tuple[Path, str]] = []

    for entry in _tree.skill_entries(skills_root):
        if entry.frontmatter_name != entry.skill:
            pairs.append((skills_root / entry.path / "SKILL.md", entry.skill))

    return pairs


def missing_category_descriptions(skills_root: Path) -> list[Path]:
    """The category dirs whose ``DESCRIPTION.md`` a repair would create.

    Declared DM2 asset containers are exempt: a repair never writes a
    ``DESCRIPTION.md`` into an asset container.
    """
    assets = _assets_container(skills_root)
    return [
        category / CATEGORY_DESCRIPTION_FILENAME
        for category in _tree.category_dirs(skills_root)
        if not (category / CATEGORY_DESCRIPTION_FILENAME).exists()
        and category.name not in assets
    ]


def validate_category_name(name: str) -> None:
    """The category-shape gate, verbatim from the original ``librarian.py``."""
    if not NAME_RE.match(name) or "--" in name or not (NAME_MIN <= len(name) <= NAME_MAX):
        raise CategoryNameError(
            "Category name must be lowercase a-z, 0-9, hyphens, 2-64 chars, "
            "no leading/trailing hyphen or double hyphen."
        )


def resolve_skill_dir(skill_ref: str, skills_root: Path) -> Path:
    """Resolve a ``category/skill`` or bare ``skill`` reference to its folder.

    Verbatim resolution order from the original ``librarian.py``:
    absolute paths; then ``category/skill`` under the root; then a bare
    name searched across every category; then the cwd-relative path;
    then the root-relative path. The first candidate that is a directory
    containing ``SKILL.md`` wins.
    """
    p = Path(skill_ref)
    candidates: list[Path] = []

    if p.is_absolute():
        candidates.append(p)
    else:
        if len(p.parts) == 2:
            candidates.append(skills_root / p)

        if len(p.parts) == 1:
            for category in _tree.category_dirs(skills_root):
                candidates.append(category / p)

        candidates.append(Path.cwd() / p)
        candidates.append(skills_root / p)

    for candidate in candidates:
        candidate = Path(candidate).resolve()
        if candidate.is_dir() and (candidate / "SKILL.md").exists():
            return candidate

    raise SkillNotFoundError(
        f"Could not find skill directory with SKILL.md: {skill_ref}"
    )


def plan_weed(root: Path) -> MutationPlan:
    """The weeding report body, without the ``Weeding report:`` header."""
    skills_root = root
    entries = _tree.skill_entries(skills_root)
    summaries = _tree.category_summaries(entries, skills_root)
    assets = _assets_container(skills_root)

    name_map: dict[str, list[str]] = {}
    desc_map: dict[str, list[str]] = {}

    for entry in entries:
        name_map.setdefault(entry.skill, []).append(entry.path)
        if entry.description:
            desc_map.setdefault(entry.description, []).append(entry.path)

    lines: list[str] = []

    for name, paths in sorted(name_map.items()):
        if len(paths) > 1:
            lines.append(
                f"- duplicate-skill-name: '{name}' appears in: "
                f"{', '.join(sorted(paths))}"
            )

    for description, paths in sorted(desc_map.items()):
        if len(paths) > 1:
            short = description if len(description) <= 80 else description[:77] + "..."
            lines.append(
                f"- duplicate-description: '{short}' appears in: "
                f"{', '.join(sorted(paths))}"
            )

    for summary in summaries:
        if summary.category in assets:
            continue
        if summary.skill_count == 0:
            lines.append(f"- empty-category: {summary.category}")
        if not summary.description_file_exists:
            lines.append(f"- missing-category-description: {summary.category}")

    return MutationPlan(kind="weed", lines=tuple(lines), root=skills_root)


def plan_repair(root: Path) -> MutationPlan:
    """The mechanical repairs the old ``librarian.py repair`` applied."""
    skills_root = root
    steps: list[MutationStep] = []
    lines: list[str] = []

    for skill_md, expected_name in name_mismatch_repairs(skills_root):
        line = f"Fixed name in {skill_md.parent.name}/SKILL.md"
        lines.append(line)
        steps.append(
            MutationStep(
                action="rewrite-name",
                description=line,
                source=skill_md,
                value=expected_name,
            )
        )

    for desc_file in missing_category_descriptions(skills_root):
        category = desc_file.parent.name
        description = f"Skills in the {category} category."
        line = (
            f"Created {category}/DESCRIPTION.md "
            f"(would write: {_yaml_quote(description)})"
        )
        lines.append(line)
        steps.append(
            MutationStep(
                action="create-description",
                description=line,
                destination=desc_file,
                value=description,
            )
        )

    return MutationPlan(
        kind="repair",
        steps=tuple(steps),
        lines=tuple(lines),
        root=skills_root,
    )

def atomic_write_json(path: Path, payload: object) -> None:
    """Atomically write ``payload`` as JSON to ``path`` (temp + os.replace).

    Cross-process lock on POSIX via ``fcntl.flock`` and on Windows via
    ``msvcrt.locking`` so concurrent writers never interleave or tear
    the file. Fails closed: I/O or lock failures raise ``OSError``
    (the same error type neighboring mutation helpers raise) rather than
    silently corrupting a sidecar.
    """
    if path.parent.is_dir():
        tmp = path.with_name(path.name + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as handle:
                _tree.cross_process_lock(handle)
                json.dump(payload, handle, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
    else:
        raise OSError(f"Cannot write JSON outside a directory: {path.parent}")