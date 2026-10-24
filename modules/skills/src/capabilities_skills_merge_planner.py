"""Skills merge planner capability (AES capabilities layer).

Read-only planning: builds the plan ``skill-lifecycle`` executes when two
skills overlap. Nothing here moves a file — the plan names the surviving
folder, the absorbed folder, the destination of every absorbed file, and
every reference that must be rewritten because it points at the absorbed
path.

The rule set is ``skill-lifecycle/SKILL.md`` §Merge Rules: survival by
frontmatter ``name:`` matching the directory name (a ``name-mismatch`` is
a stale-by-definition name), ties broken by the more complete body (file
count, then description length, then alphabetical for determinism); the
absorbed folder's non-conflicting assets move into the survivor; the
absorbed path disappears, so every catalog row and every reference to it
is listed for rewriting. The survivor keeps its category: a merge is a
deduplication, not a relocation.
"""

from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsMergePlannerProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import MergePlan
from modules.shared.src.skills.taxonomy_skills_error import (
    MutationConflictError,
    SkillNotFoundError,
    SkillsUsageError,
)
from modules.shared.src.skills.taxonomy_skills_vo import SkillsRoot
from modules.shared.src.utility_skills_tree import (
    iter_files,
    iter_markdown_files,
    relpath,
    skill_entries,
)

__all__ = ["SkillsMergePlanner", "parse_ref"]

#: Subdirectories a merged body keeps as-is: scenario material and
#: category metadata are content, not build output.
_KEEP_DIRS = ("references", "scripts")

#: Files never moved into the survivor: the identity card belongs to the
#: surviving folder, and a stale frontmatter in the absorbed folder would
#: produce two ``name:`` keys if it landed beside the survivor's.
_SKIP_FILES = ("SKILL.md", "SKILL.md.archived")


def parse_ref(reference: str) -> tuple[str, str]:
    """Split a ``category/skill`` reference into its two parts.

    A bare ``skill`` form is rejected rather than searched across
    categories: a merge operates on two exact folders, and a one-part
    reference would make ``merge-plan a b`` silently pick the first folder
    named ``a`` in a category the caller did not name.
    """
    parts = reference.split("/")
    if len(parts) != 2 or not all(parts):
        raise SkillsUsageError(
            f"Skill reference must be 'category/skill': {reference!r} "
            "(merge-plan needs both parts — a bare name is ambiguous)"
        )
    return parts[0], parts[1]


def _load(skills_root: Path, category: str, skill: str):
    """Load one ``category/skill`` entry; fail with the legacy message when absent."""
    entry = next(
        (
            candidate
            for candidate in skill_entries(skills_root)
            if candidate.category == category and candidate.skill == skill
        ),
        None,
    )
    if entry is None:
        raise SkillNotFoundError(
            f"Could not find skill directory with SKILL.md: {category}/{skill}"
        )
    return entry


def _completeness(entry, skills_root: Path) -> tuple[int, int, str]:
    """The tie-break signal: file count, then description length, then name."""
    folder = skills_root / entry.path
    file_count = sum(1 for _ in iter_files(folder))
    return (file_count, len(entry.description), entry.skill)


def _asset_moves(source: Path, dest: Path, skills_root: Path) -> list[tuple[str, str]]:
    """The files that move from an absorbed folder into the survivor.

    ``references/`` and ``scripts/`` contents move under their own names;
    any top-level file that is not the identity card moves too. A name
    that already exists at the destination is a conflict the plan reports
    rather than silently overwriting.
    """
    moves: list[tuple[str, str]] = []

    for child in sorted(source.iterdir()):
        if child.name in _SKIP_FILES:
            continue

        if child.is_dir() and child.name in _KEEP_DIRS:
            for leaf in iter_files(child):
                target = dest / child.name / leaf.relative_to(child)
                if target.exists():
                    raise MutationConflictError(
                        f"Conflict merging {relpath(leaf, skills_root)}: "
                        f"{relpath(target, skills_root)} already exists"
                    )
                moves.append((str(leaf), str(target)))
            continue

        if child.is_file():
            target = dest / child.name
            if target.exists():
                raise MutationConflictError(
                    f"Conflict merging {relpath(child, skills_root)}: "
                    f"{relpath(target, skills_root)} already exists"
                )
            moves.append((str(child), str(target)))

    return moves


def _references_to(skills_root: Path, path: str) -> list[str]:
    """Files under the skills root that mention an absorbed path or skill name."""
    skill_name = path.split("/")[-1]
    mentions: list[str] = []

    for md in sorted(iter_markdown_files(skills_root)):
        if md.name == "CATALOG.md":
            continue

        rel = md.relative_to(skills_root).as_posix()
        if rel.startswith("_archive/") or rel.split("/")[0] in {"_archive"}:
            continue

        try:
            text = md.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue

        if path in text or f"/{skill_name}" in text or f"]{skill_name}]" in text:
            mentions.append(rel)

    return mentions


def _category_left_empty(skills_root: Path, absorbed) -> str | None:
    """The absorbed skill's category if removing it empties the category."""
    folder = skills_root / absorbed.category
    remaining = [
        child
        for child in sorted(folder.iterdir())
        if child.is_dir()
        and (child / "SKILL.md").exists()
        and child.name != absorbed.skill
    ]
    return absorbed.category if not remaining else None


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsMergePlanner(ISkillsMergePlannerProtocol):
    """Builds (and renders) read-only merge plans."""

    # ─── Block 2: Protocol Method Implementations ─────────────
    def plan(self, ref_a: str, ref_b: str, root: SkillsRoot) -> MergePlan:
        """Build the plan for merging two ``category/skill`` references."""
        skills_root = Path(root)
        cat_a, skill_a = parse_ref(ref_a)
        cat_b, skill_b = parse_ref(ref_b)

        entry_a = _load(skills_root, cat_a, skill_a)
        entry_b = _load(skills_root, cat_b, skill_b)

        survives_a = entry_a.frontmatter_name == entry_a.skill
        survives_b = entry_b.frontmatter_name == entry_b.skill

        if survives_a != survives_b:
            survivor, absorbed = (
                (entry_a, entry_b) if survives_a else (entry_b, entry_a)
            )
            survival_reason = (
                "frontmatter `name:` matches the directory name; the other skill's "
                "name is stale (rule: name-mismatch)"
            )
        else:
            survivor, absorbed = sorted(
                (entry_a, entry_b),
                key=lambda entry: _completeness(entry, skills_root),
                reverse=True,
            )
            survival_reason = (
                "both `name:` values match (or neither does); the more complete "
                "body wins (file count, then description length)"
            )

        source = skills_root / absorbed.path
        dest = skills_root / survivor.path
        moves = _asset_moves(source, dest, skills_root)

        rewrites: list[dict[str, str]] = [
            {
                "kind": "catalog-row",
                "from": (
                    f"skills/CATALOG.md row '{absorbed.skill}' at {absorbed.path}"
                ),
                "to": (
                    f"{survivor.path} (or deletion — the survivor's row already exists)"
                ),
            }
        ]

        for reference in _references_to(skills_root, absorbed.path):
            rewrites.append(
                {
                    "kind": "reference",
                    "from": reference,
                    "to": f"{reference} mentions {absorbed.path} or {absorbed.skill}",
                }
            )

        return MergePlan(
            survivor=relpath(dest, skills_root),
            absorbed=relpath(source, skills_root),
            survival_reason=survival_reason,
            moves=tuple(
                (
                    relpath(Path(src), skills_root),
                    relpath(Path(dst), skills_root),
                )
                for src, dst in moves
            ),
            rewrites=tuple(rewrites),
            category_after=survivor.category,
            empty_category_after=(
                _category_left_empty(skills_root, absorbed)
                if survivor.category != absorbed.category
                else None
            ),
        )

    def render(self, plan: MergePlan) -> tuple[str, ...]:
        """Render a merge plan as the readable markdown report."""
        lines = [
            "# Merge plan",
            "",
            f"- Survivor: `{plan.survivor}`",
            f"- Absorbed: `{plan.absorbed}`",
            f"- Survival: {plan.survival_reason}",
            "",
            "## Moves",
            "",
        ]

        if plan.moves:
            for source, dest in plan.moves:
                lines.append(f"- `{source}` -> `{dest}`")
        else:
            lines.append(
                "- (none — the absorbed skill has no references/ or scripts/ assets)"
            )

        lines.extend(["", "## Rewrite", ""])
        if plan.rewrites:
            for rewrite in plan.rewrites:
                lines.append(f"- [{rewrite['kind']}] {rewrite['from']}")
                lines.append(f"  -> {rewrite['to']}")
        else:
            lines.append("- (none)")

        lines.extend(
            [
                "",
                "## Delete",
                "",
                f"- `{plan.absorbed}` — absorbed into `{plan.survivor}`",
                "",
                "## After",
                "",
                f"- Category: `{plan.category_after}`",
            ]
        )

        if plan.empty_category_after:
            lines.append(
                f"- Empty category cleanup: delete `{plan.empty_category_after}` "
                "and its `DESCRIPTION.md` (no skill folders remain)"
            )
        else:
            lines.append("- Empty category cleanup: (none)")

        return tuple(lines)
