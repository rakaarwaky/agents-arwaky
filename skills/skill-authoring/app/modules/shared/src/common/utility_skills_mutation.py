"""Skills mutation utilities (AES utility layer).

Shared helpers for the mover, archiver, and creator capabilities:
skill-dir resolution, category-name validation, containment assertion,
and the weed / repair report generators. These were split out of the
retired ``capabilities_skills_mutator`` so each mutation capability can
depend on the shared kernel without a sibling import.

The skill-tree walkers this file needs are inlined here (private) so the
module stays self-contained: utility files must not import one another
(AES201). The public kernel modules ``utility_skills_markdown`` /
``utility_skills_tree`` keep their own copies for the capabilities that
consume them.
"""
from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator
from pathlib import Path
from types import ModuleType

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows has no fcntl
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX has no msvcrt
    msvcrt = None

from shared.src.skills_design.taxonomy_skills_constant import (
    ARCHIVE_DIRNAME,
    ASSETS_MARKER_FILENAME,
    CATEGORY_DESCRIPTION_FILENAME,
    IGNORED_CATEGORY_DIRS,
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)
from shared.src.skills_design.taxonomy_skills_entity import (
    CategorySummary,
    SkillEntry,
)
from shared.src.skills_design.taxonomy_skills_error import (
    CategoryNameError,
    SkillNotFoundError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.skills_design.taxonomy_skills_vo import (
    MutationPlan,
    MutationStep,
)

# ─── Inlined tree walkers (private; utility files stay independent, AES201) ──

yaml: ModuleType | None = None
try:
    import yaml as _yaml

    yaml = _yaml
except ImportError:  # pragma: no cover - exercised by the S8 test
    yaml = None


def _clean_one_line(value: object) -> str:
    """Collapse whitespace to single spaces and strip the edges."""
    return " ".join(str(value).split()).strip()


def _yaml_quote(value: object) -> str:
    """Quote a YAML scalar the way the original ``librarian.py`` did."""
    return json.dumps(str(value), ensure_ascii=False)


def _category_dirs(skills_root: Path) -> Iterator[Path]:
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


def _parse_frontmatter(path: Path) -> dict[str, object]:
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
        except yaml.YAMLError:
            # Broken frontmatter degrades to the fallback parser below.
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


def _assets_container(skills_root: Path) -> set[str]:
    """Category names that carry a declared DM2 asset-container marker."""
    declared = set()
    for category in _category_dirs(skills_root):
        marker = category / ASSETS_MARKER_FILENAME
        if not marker.is_file():
            continue
        frontmatter = _parse_frontmatter(marker)
        if frontmatter.get("kind") == "assets":
            declared.add(category.name)
    return declared


def _skill_entries(skills_root: Path) -> list[SkillEntry]:
    """All discoverable skills: ``category/*/SKILL.md`` with frontmatter."""
    entries = []

    for category in _category_dirs(skills_root):
        for skill_md in sorted(category.glob("*/SKILL.md")):
            skill_dir = skill_md.parent
            frontmatter = _parse_frontmatter(skill_md)

            entries.append(
                SkillEntry(
                    skill=skill_dir.name,
                    frontmatter_name=_clean_one_line(
                        frontmatter.get("name", skill_dir.name)
                    ),
                    category=category.name,
                    description=_clean_one_line(frontmatter.get("description", "")),
                    when_to_use=_clean_one_line(frontmatter.get("when-to-use", "")),
                    path=f"{category.name}/{skill_dir.name}",
                )
            )

    return entries


def _category_summaries(
    entries: Iterable[SkillEntry], skills_root: Path
) -> list[CategorySummary]:
    """Per-category description state and skill counts.

    ``entries`` is materialized once because it is re-iterated per
    category; a generator passed here would be consumed by the first
    category and silently zero every later category's count.
    """
    entries = list(entries)
    summaries = []

    for category in _category_dirs(skills_root):
        desc_file = category / CATEGORY_DESCRIPTION_FILENAME
        description = ""
        exists = desc_file.exists()

        if exists:
            frontmatter = _parse_frontmatter(desc_file)
            description = _clean_one_line(frontmatter.get("description", ""))

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

__all__ = [
    "archive_root",
    "assert_within_root",
    "atomic_write_json",
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
        f"---\ndescription: {_yaml_quote(description)}\n---\n",
        encoding="utf-8",
    )
    return True


def name_mismatch_repairs(skills_root: Path) -> list[tuple[Path, str]]:
    """The ``(skill_md, expected_name)`` pairs a repair would rewrite."""
    pairs: list[tuple[Path, str]] = []

    for entry in _skill_entries(skills_root):
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
        for category in _category_dirs(skills_root)
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
            for category in _category_dirs(skills_root):
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
    entries = _skill_entries(skills_root)
    summaries = _category_summaries(entries, skills_root)
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
                _lock(handle)
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

def _lock(handle) -> None:
    """Take an exclusive, blocking lock on the open file handle."""
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    elif msvcrt is not None:
        handle.flush()
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1 << 31 - 1)
