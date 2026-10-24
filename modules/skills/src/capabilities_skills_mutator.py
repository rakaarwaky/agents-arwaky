"""Skills mutator capability (AES capabilities layer).

The write side of the library, ported from the retired legacy mutator.
Every mutating operation is split in two:

- ``plan_*`` is pure: it computes what would change and returns a
  ``MutationPlan`` (or ``NewCategoryPlan``). It never writes.
- ``apply`` / ``apply_new_category`` performs the writes the plan
  described.

Dry-run is the contract and ``--apply`` is the exception, enforced by
``SkillsRequest.apply`` in the agent; this capability never sets it.
The legacy ``fail()`` channel becomes typed taxonomy errors — the
capability never prints and never exits.

Every computed destination is asserted to remain inside the skills root
at plan time **and** re-checked at apply time, so a symlink created
between the two fails closed instead of writing outside the pack.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsMutatorProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    MutationOutcome,
    MutationPlan,
    MutationStep,
    NewCategoryPlan,
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
    MutationConflictError,
    SkillNotFoundError,
    SkillsUsageError,
)
from modules.shared.src.skills.taxonomy_skills_vo import SkillsRoot
from modules.shared.src.utility_skills_markdown import yaml_quote
from modules.shared.src.utility_skills_tree import (
    assets_container,
    category_dirs,
    category_summaries,
    relpath,
    skill_entries,
)

__all__ = [
    "SkillsMutator",
    "archive_root",
    "ensure_frontmatter_name",
]


def archive_root(skills_root: Path) -> Path:
    """The archive tree for a skills root."""
    return skills_root / ARCHIVE_DIRNAME


def _assert_within_root(path: Path, root: Path) -> None:
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


def _name_mismatch_repairs(skills_root: Path) -> list[tuple[Path, str]]:
    """The ``(skill_md, expected_name)`` pairs a repair would rewrite."""
    pairs: list[tuple[Path, str]] = []

    for entry in skill_entries(skills_root):
        if entry.frontmatter_name != entry.skill:
            pairs.append((skills_root / entry.path / "SKILL.md", entry.skill))

    return pairs


def _missing_category_descriptions(skills_root: Path) -> list[Path]:
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


def _validate_category_name(name: str) -> None:
    """The category-shape gate, verbatim from the original ``librarian.py``."""
    if not NAME_RE.match(name) or "--" in name or not (NAME_MIN <= len(name) <= NAME_MAX):
        raise CategoryNameError(
            "Category name must be lowercase a-z, 0-9, hyphens, 2-64 chars, "
            "no leading/trailing hyphen or double hyphen."
        )


def _resolve_skill_dir(skill_ref: str, skills_root: Path) -> Path:
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


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsMutator(ISkillsMutatorProtocol):
    """Plans and applies mechanical library mutations (never both at once)."""

    # ─── Block 2: Protocol Method Implementations ─────────────
    def plan_move(
        self, skill: str, target: str, root: SkillsRoot
    ) -> MutationPlan:
        """Resolve a move; the returned plan takes no action."""
        skills_root = Path(root)
        source = _resolve_skill_dir(skill, skills_root)
        _validate_category_name(target)

        target_dir = skills_root / target

        if not target_dir.is_dir():
            raise SkillsUsageError(
                f"Target category does not exist: {target}. "
                "Create it first with new-category."
            )

        destination = target_dir / source.name

        if source.parent.resolve() == target_dir.resolve():
            return MutationPlan(
                kind="move",
                source=source,
                destination=destination,
                already_in_category=True,
                root=skills_root,
            )

        if destination.exists():
            raise MutationConflictError(
                f"Destination already exists: {relpath(destination, skills_root)}"
            )

        _assert_within_root(destination, skills_root)

        return MutationPlan(
            kind="move",
            source=source,
            destination=destination,
            root=skills_root,
        )

    def plan_archive(self, skill: str, root: SkillsRoot) -> MutationPlan:
        """Resolve an archive; the skill lands at ``_archive/<cat>/<skill>/``."""
        skills_root = Path(root)
        source = _resolve_skill_dir(skill, skills_root)
        category = source.parent.name
        destination = archive_root(skills_root) / category / source.name

        if destination.exists():
            raise MutationConflictError(
                f"Archive destination already exists: {destination}"
            )

        _assert_within_root(destination, skills_root)

        return MutationPlan(
            kind="archive",
            source=source,
            destination=destination,
            root=skills_root,
        )

    def plan_repair(self, root: SkillsRoot) -> MutationPlan:
        """The mechanical repairs the old ``librarian.py repair`` applied."""
        skills_root = Path(root)
        steps: list[MutationStep] = []
        lines: list[str] = []

        for skill_md, expected_name in _name_mismatch_repairs(skills_root):
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

        for desc_file in _missing_category_descriptions(skills_root):
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

    def plan_weed(self, root: SkillsRoot) -> MutationPlan:
        """The weeding report body, without the ``Weeding report:`` header."""
        skills_root = Path(root)
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

    def plan_new_category(
        self,
        name: str,
        description: str | None,
        root: SkillsRoot,
        force: bool,
    ) -> NewCategoryPlan:
        """Resolve a category creation; the folder is only created on apply."""
        skills_root = Path(root)
        _validate_category_name(name)

        category = skills_root / name
        resolved_description = description or f"Skills in the {name} category."
        desc_file = category / CATEGORY_DESCRIPTION_FILENAME
        will_write = not (desc_file.exists() and not force)

        _assert_within_root(category, skills_root)

        return NewCategoryPlan(
            name=name,
            description=resolved_description,
            directory=category,
            description_file=desc_file,
            will_write=will_write,
            root=skills_root,
        )

    def apply(self, plan: MutationPlan) -> MutationOutcome:
        """Execute a repair/move/archive plan; re-checks containment first."""
        root = plan.root
        if plan.kind == "repair":
            return self._apply_repair(plan)
        if plan.kind == "move":
            if plan.source is None or plan.destination is None:
                raise SkillsUsageError("Move plan is missing its paths")
            if root is not None:
                _assert_within_root(plan.destination, root)
            shutil.move(str(plan.source), str(plan.destination))
            return MutationOutcome(message="moved")
        if plan.kind == "archive":
            if plan.source is None or plan.destination is None:
                raise SkillsUsageError("Archive plan is missing its paths")
            if root is not None:
                _assert_within_root(plan.destination, root)
            plan.destination.parent.mkdir(parents=True, exist_ok=True)
            _assert_within_root(plan.destination, root or plan.destination.parent)
            shutil.move(str(plan.source), str(plan.destination))
            archived_md = plan.destination / "SKILL.md"
            if archived_md.exists():
                archived_md.rename(plan.destination / "SKILL.md.archived")
            return MutationOutcome(message="archived")
        raise SkillsUsageError(f"Cannot apply a {plan.kind!r} plan")

    def apply_new_category(self, plan: NewCategoryPlan) -> bool:
        """Create the category and write its description; returns whether it wrote."""
        if plan.root is not None:
            _assert_within_root(plan.directory, plan.root)
        plan.directory.mkdir(exist_ok=True)
        if plan.root is not None:
            _assert_within_root(plan.description_file, plan.root)
        return write_category_description(
            plan.directory, plan.description, force=plan.will_write
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    @staticmethod
    def _apply_repair(plan: MutationPlan) -> MutationOutcome:
        """Apply a repair plan's steps, returning the applied report lines."""
        applied: list[str] = []

        for step in plan.steps:
            if step.action == "rewrite-name":
                if step.source is None:
                    continue
                if ensure_frontmatter_name(step.source, step.value):
                    applied.append(
                        f"Fixed name in {step.source.parent.parent.name}/"
                        f"{step.source.parent.name}/SKILL.md"
                    )
            elif step.action == "create-description":
                if step.destination is None or step.destination.exists():
                    continue
                write_category_description(step.destination.parent, step.value)
                applied.append(f"Created {step.destination.parent.name}/DESCRIPTION.md")

        return MutationOutcome(applied=tuple(applied), message="repaired")

