"""Skills mutation utilities (AES utility layer).

Shared helpers for the mover, archiver, and creator capabilities:
skill-dir resolution, category-name validation, containment assertion,
and the weed / repair report generators. These were split out of the
retired ``capabilities_skills_mutator`` so each mutation capability can
depend on the shared kernel without a sibling import.
"""

from __future__ import annotations

from pathlib import Path

from modules.shared.src.common.utility_skills_markdown import yaml_quote
from modules.shared.src.common.utility_skills_tree import (
    assets_container,
    category_dirs,
    category_summaries,
    skill_entries,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    MutationPlan,
    MutationStep,
)
from modules.shared.src.skills.taxonomy_skills_constant import (
    ARCHIVE_DIRNAME,
    CATEGORY_DESCRIPTION_FILENAME,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)
from modules.shared.src.skills.taxonomy_skills_error import (
    CategoryNameError,
    SkillNotFoundError,
    SkillsUsageError,
)

__all__ = [
    "archive_root",
    "assert_within_root",
    "ensure_frontmatter_name",
    "missing_category_descriptions",
    "name_mismatch_repairs",
    "plan_repair",
    "plan_weed",
    "resolve_skill_dir",
    "validate_category_name",
    "write_category_description",
]


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


def ensure_frontmatter_name(skill_md: Path, expected_name: str) -> bool:
    """Rewrite ``name:`` in ``skill_md`` to ``expected_name``.

    Verbatim from the original ``librarian.py``: inserts a minimal
    frontmatter block when the file has none. Returns whether the file
    changed.
    """
    text = skill_md.read_text(encoding="utf-8-sig", errors="replace")
    stripped = text.lstrip()

    if not stripped.startswith("---"):
        new_text = f"---\nname: {expected_name}\ndescription: TODO\n---\n\n{text}"
        skill_md.write_text(new_text, encoding="utf-8")
        return True

    parts = stripped.split("---", 2)
    if len(parts) < 3:
        return False

    fm_lines = parts[1].splitlines()
    replaced = False

    for i, line in enumerate(fm_lines):
        if line.startswith("name:"):
            fm_lines[i] = f"name: {expected_name}"
            replaced = True
            break

    if not replaced:
        fm_lines.insert(0, f"name: {expected_name}")

    fm_body = "\n".join(fm_lines).strip("\n")
    body = parts[2]
    new_text = f"---\n{fm_body}\n---{body}"

    skill_md.write_text(new_text, encoding="utf-8")
    return True


def write_category_description(
    category: Path, description: str, force: bool = False
) -> bool:
    """Write ``category/DESCRIPTION.md``; keep an existing one unless ``force``."""
    desc_file = category / CATEGORY_DESCRIPTION_FILENAME

    if desc_file.exists() and not force:
        return False

    desc_file.write_text(
        f"---\ndescription: {yaml_quote(description)}\n---\n",
        encoding="utf-8",
    )
    return True


def name_mismatch_repairs(skills_root: Path) -> list[tuple[Path, str]]:
    """The ``(skill_md, expected_name)`` pairs a repair would rewrite."""
    pairs: list[tuple[Path, str]] = []

    for entry in skill_entries(skills_root):
        if entry.frontmatter_name != entry.skill:
            pairs.append((skills_root / entry.path / "SKILL.md", entry.skill))

    return pairs


def missing_category_descriptions(skills_root: Path) -> list[Path]:
    """The category dirs whose ``DESCRIPTION.md`` a repair would create.

    Declared DM2 asset containers are exempt: a repair never writes a
    ``DESCRIPTION.md`` into an asset container.
    """
    assets = assets_container(skills_root)
    return [
        category / CATEGORY_DESCRIPTION_FILENAME
        for category in category_dirs(skills_root)
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
            for category in category_dirs(skills_root):
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
    entries = skill_entries(skills_root)
    summaries = category_summaries(entries, skills_root)
    assets = assets_container(skills_root)

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
            f"(would write: {yaml_quote(description)})"
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
