"""Mutations and weeding reports (design §5.5, §6.1).

The write side of the library. Every mutating operation is a single
``plan_*`` function that computes what would change and returns a list of
human-readable steps; the caller decides whether to execute them. All
write paths are gated behind ``--apply`` by ``cli.py`` — nothing in this
module writes on import or on a read-only call.

``fail`` lives here because it is the shared error channel: every module
reports usage/input errors through it and ``cli.py`` translates the exit
code (design §6.1 — ``fail`` keeps the legacy ``ERROR: …`` stderr line so
the old scripts' error output survives byte-for-byte).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import model
from skill_rules import NAME_RE

__all__ = [
    "ARCHIVE_DIRNAME",
    "apply_archive",
    "apply_move",
    "apply_new_category",
    "apply_repairs",
    "archive_plan",
    "archive_root",
    "ensure_frontmatter_name",
    "fail",
    "missing_category_descriptions",
    "move_plan",
    "name_mismatch_repairs",
    "new_category_plan",
    "relpath",
    "repair_plan",
    "weed_report",
    "write_category_description",
    "yaml_quote",
]

#: Archive directory, verbatim from the original ``librarian.py`` and the
#: SSOT's ``IGNORED_CATEGORY_DIRS`` (the walker skips it).
ARCHIVE_DIRNAME = "_archive"


def fail(message: str) -> None:
    """Print the legacy ``ERROR: …`` line to stderr and exit nonzero."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def relpath(path: Path, skills_root: Path) -> str:
    """A skills-root-relative path when possible, else the absolute one."""
    try:
        return str(path.relative_to(skills_root))
    except ValueError:
        return str(path)


def yaml_quote(value: object) -> str:
    """Quote a YAML scalar the way the original ``librarian.py`` did."""
    return json.dumps(str(value), ensure_ascii=False)


def archive_root(skills_root: Path) -> Path:
    """The archive tree for a skills root."""
    return skills_root / ARCHIVE_DIRNAME


# ── Read-only reports ──────────────────────────────────────────────────


def weed_report(skills_root: Path) -> list[str]:
    """The weeding report body, without the ``Weeding report:`` header.

    Returns the lines the old ``librarian.py weed`` printed between the
    header and the end (``No obvious weeds found.`` when clean), so the
    caller can print them identically or surface them as JSON issues.
    """
    entries = model.skill_entries(skills_root)
    categories = model.category_summaries(entries, skills_root)

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
                f"- duplicate-skill-name: '{name}' appears in: {', '.join(sorted(paths))}"
            )

    for description, paths in sorted(desc_map.items()):
        if len(paths) > 1:
            short = description if len(description) <= 80 else description[:77] + "..."
            lines.append(
                f"- duplicate-description: '{short}' appears in: {', '.join(sorted(paths))}"
            )

    for cat in categories:
        if cat.skill_count == 0:
            lines.append(f"- empty-category: {cat.category}")

        if not cat.description_file_exists:
            lines.append(f"- missing-category-description: {cat.category}")

    return lines


# ── Frontmatter/category file helpers ─────────────────────────────────


def ensure_frontmatter_name(skill_md: Path, expected_name: str) -> bool:
    """Rewrite ``name:`` in ``skill_md`` to ``expected_name``.

    Verbatim from the original ``librarian.py`` (the caller of
    ``repair``): inserts a minimal frontmatter block when the file has
    none. Returns whether the file changed.
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


def write_category_description(category: Path, description: str, force: bool = False) -> bool:
    """Write ``category/DESCRIPTION.md``; keep an existing one unless ``force``."""
    desc_file = category / model.CATEGORY_DESCRIPTION_FILENAME

    if desc_file.exists() and not force:
        return False

    desc_file.write_text(
        f"---\ndescription: {yaml_quote(description)}\n---\n",
        encoding="utf-8",
    )
    return True


# ── Mutations: each returns the steps it would take ───────────────────


def name_mismatch_repairs(skills_root: Path) -> list[tuple[Path, str]]:
    """The ``(skill_md, expected_name)`` pairs a repair would rewrite.

    Pure detection: ``ensure_frontmatter_name`` writes, so a dry-run must
    not call it — this function reads the frontmatter and reports the
    mismatch instead. ``repair --apply`` hands each pair to the writer.
    """
    pairs: list[tuple[Path, str]] = []

    for entry in model.skill_entries(skills_root):
        if entry.frontmatter_name != entry.skill:
            pairs.append((skills_root / entry.path / "SKILL.md", entry.skill))

    return pairs


def missing_category_descriptions(skills_root: Path) -> list[Path]:
    """The category dirs whose ``DESCRIPTION.md`` a repair would create."""
    return [
        category / model.CATEGORY_DESCRIPTION_FILENAME
        for category in model.category_dirs(skills_root)
        if not (category / model.CATEGORY_DESCRIPTION_FILENAME).exists()
    ]


def repair_plan(skills_root: Path) -> list[str]:
    """The mechanical repairs the old ``librarian.py repair`` applied.

    Read-only: returns the step lines and touches nothing. ``cli.py``
    executes them (plus the catalog rebuild) under ``--apply``.
    """
    repaired: list[str] = [
        f"Fixed name in {skill_md.parent.name}/SKILL.md"
        for skill_md, _ in name_mismatch_repairs(skills_root)
    ]

    for category in model.category_dirs(skills_root):
        desc_file = category / model.CATEGORY_DESCRIPTION_FILENAME
        if not desc_file.exists():
            repaired.append(
                f"Created {category.name}/DESCRIPTION.md "
                f"(would write: {yaml_quote(f'Skills in the {category.name} category.')})"
            )

    return repaired


def _validate_category_name(name: str) -> None:
    """The category-shape gate, verbatim from the original ``librarian.py``."""
    if (
        not NAME_RE.match(name)
        or "--" in name
        or not (2 <= len(name) <= 64)
    ):
        fail(
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
            for category in model.category_dirs(skills_root):
                candidates.append(category / p)

        candidates.append(Path.cwd() / p)
        candidates.append(skills_root / p)

    for candidate in candidates:
        candidate = Path(candidate).resolve()
        if candidate.is_dir() and (candidate / "SKILL.md").exists():
            return candidate

    fail(f"Could not find skill directory with SKILL.md: {skill_ref}")


def apply_repairs(skills_root: Path) -> list[str]:
    """Execute the mechanical repairs; returns the applied-step lines.

    The exact writes the old ``librarian.py repair`` performed: rewrite a
    mismatched frontmatter ``name:``, then create the missing category
    ``DESCRIPTION.md`` files. Returns the same step strings
    ``repair_plan`` previewed, so the dry-run report and the applied
    report name the same work.
    """
    applied: list[str] = []

    for skill_md, expected_name in name_mismatch_repairs(skills_root):
        if ensure_frontmatter_name(skill_md, expected_name):
            applied.append(f"Fixed name in {skill_md.parent.parent.name}/{skill_md.parent.name}/SKILL.md")

    for desc_file in missing_category_descriptions(skills_root):
        category = desc_file.parent
        write_category_description(
            category, f"Skills in the {category.name} category."
        )
        applied.append(f"Created {category.name}/DESCRIPTION.md")

    return applied


def move_plan(
    skill_ref: str, target_category: str, skills_root: Path
) -> tuple[Path, Path]:
    """Resolve a move; returns ``(source, destination)``.

    Fails with the legacy messages when the skill is unresolvable, when
    the target category does not exist, when the destination exists, or
    when the skill already lives in the target category (the original
    prints ``Skill already in category: X`` — surfaced as the empty-plan
    case ``cli.py`` prints verbatim). Takes no action.
    """
    source = resolve_skill_dir(skill_ref, skills_root)
    _validate_category_name(target_category)

    target = skills_root / target_category

    if not target.is_dir():
        fail(
            f"Target category does not exist: {target_category}. "
            "Create it first with new-category."
        )

    dest = target / source.name

    if dest.exists():
        fail(f"Destination already exists: {relpath(dest, skills_root)}")

    return source, dest


def archive_plan(skill_ref: str, skills_root: Path) -> tuple[Path, Path]:
    """Resolve an archive; returns ``(source, archive_destination)``.

    Verbatim rule from the original ``librarian.py``: the skill moves to
    ``_archive/<category>/<skill>/`` and its ``SKILL.md`` is renamed
    ``SKILL.md.archived`` once it lands there.
    """
    source = resolve_skill_dir(skill_ref, skills_root)
    category = source.parent.name
    dest = archive_root(skills_root) / category / source.name

    if dest.exists():
        fail(f"Archive destination already exists: {dest}")

    return source, dest


def new_category_plan(
    name: str, description: str | None, skills_root: Path, force: bool = False
) -> tuple[Path, str, bool]:
    """Resolve a category creation; returns ``(category, description, will_write)``.

    ``will_write`` is False when the description file already exists and
    ``force`` is unset — the original prints ``Kept existing …`` for that
    case, and the folder itself is only created on apply.
    """
    _validate_category_name(name)

    category = skills_root / name
    description = description or f"Skills in the {name} category."

    desc_file = category / model.CATEGORY_DESCRIPTION_FILENAME
    will_write = True
    if desc_file.exists() and not force:
        will_write = False

    return category, description, will_write


def apply_move(source: Path, dest: Path) -> None:
    """Execute a resolved move."""
    shutil.move(str(source), str(dest))


def apply_archive(source: Path, dest: Path) -> None:
    """Execute a resolved archive (move + rename ``SKILL.md`` to ``.archived``)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(dest))

    archived_md = dest / "SKILL.md"
    if archived_md.exists():
        archived_md.rename(dest / "SKILL.md.archived")


def apply_new_category(category: Path, description: str, force: bool) -> bool:
    """Execute a resolved category creation; returns whether a description was written."""
    category.mkdir(exist_ok=True)
    return write_category_description(category, description, force=force)
