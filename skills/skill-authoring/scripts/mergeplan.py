"""Merge planning for ``cli merge-plan`` (design §6.1; ``prune-skills`` §Merge Rules).

Read-only planning: builds the plan ``prune-skills`` executes when two
skills overlap. Nothing here moves a file — the plan names the surviving
folder, the absorbed folder, the destination of every absorbed file, and
every reference that has to be rewritten because it points at the
absorbed path.

The rule set is ``prune-skills/SKILL.md`` §Merge Rules:
survival by frontmatter ``name:`` matching the directory name (a
``name-mismatch`` is a stale-by-definition name), ties broken by the more
complete body (file count, then description length, then alphabetical for
determinism); the absorbed folder's non-conflicting assets move into the
survivor; the absorbed path disappears, so every catalog row and every
reference to it is listed for rewriting. The survivor keeps its category:
a merge is a deduplication, not a relocation (``move`` is the relocation
tool, and chaining a relocation into a merge would hide it inside a
command whose report says "merge").
"""

from __future__ import annotations

from pathlib import Path

import model
from mutate import fail, relpath

__all__ = ["merge_plan", "parse_ref", "render_merge_plan"]

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
    reference would make ``merge-plan a b`` silently pick the first
    folder named ``a`` in a category the caller did not name.
    """
    parts = reference.split("/")
    if len(parts) != 2 or not all(parts):
        fail(
            f"Skill reference must be 'category/skill': {reference!r} "
            "(merge-plan needs both parts — a bare name is ambiguous)"
        )
    return parts[0], parts[1]


def _load(skills_root: Path, category: str, skill: str) -> model.SkillEntry:
    """Load one ``category/skill`` row; fails with the legacy message when absent."""
    entry = next(
        (
            e
            for e in model.skill_entries(skills_root)
            if e.category == category and e.skill == skill
        ),
        None,
    )
    if entry is None:
        fail(f"Could not find skill directory with SKILL.md: {category}/{skill}")
    return entry


def _completeness(entry: model.SkillEntry, skills_root: Path) -> tuple[int, int, str]:
    """The tie-break signal: file count, then description length, then name."""
    folder = skills_root / entry.path
    file_count = sum(1 for _ in folder.rglob("*") if _.is_file())
    return (file_count, len(entry.description), entry.skill)


def _asset_moves(source: Path, dest: Path) -> list[tuple[str, str]]:
    """The files that move from an absorbed folder into the survivor.

    ``references/`` and ``scripts/`` contents move under their own names;
    any top-level file that is not the identity card moves too. A name
    that already exists at the destination is a conflict the plan reports
    rather than silently overwrites.
    """
    moves: list[tuple[str, str]] = []

    for child in sorted(source.iterdir()):
        if child.name in _SKIP_FILES:
            continue

        if child.is_dir() and child.name in _KEEP_DIRS:
            for leaf in sorted(child.rglob("*")):
                if leaf.is_file():
                    target = dest / child.name / leaf.relative_to(child)
                    if target.exists():
                        fail(
                            f"Conflict merging {relpath(leaf, source.parent.parent)}: "
                            f"{relpath(target, dest.parent.parent)} already exists"
                        )
                    moves.append((str(leaf), str(target)))
            continue

        if child.is_file():
            target = dest / child.name
            if target.exists():
                fail(
                    f"Conflict merging {relpath(child, source.parent.parent)}: "
                    f"{relpath(target, dest.parent.parent)} already exists"
                )
            moves.append((str(child), str(target)))

    return moves


def merge_plan(
    ref_a: str, ref_b: str, skills_root: Path
) -> dict[str, object]:
    """Build the plan for merging ``ref_b`` into ``ref_a``'s survivor.

    The survivor is chosen on rule merit, not on argument order: the
    skill whose frontmatter ``name:`` matches its folder survives (the
    other's name is stale by definition — see ``prune-skills`` §Merge
    Rules, "Name survival"); a tie falls to the more complete body. The
    absorbed skill is always the one whose folder disappears.
    """
    cat_a, skill_a = parse_ref(ref_a)
    cat_b, skill_b = parse_ref(ref_b)

    entry_a = _load(skills_root, cat_a, skill_a)
    entry_b = _load(skills_root, cat_b, skill_b)

    survives_a = entry_a.frontmatter_name == entry_a.skill
    survives_b = entry_b.frontmatter_name == entry_b.skill

    if survives_a != survives_b:
        survivor, absorbed = (entry_a, entry_b) if survives_a else (entry_b, entry_a)
        survival_reason = (
            "frontmatter `name:` matches the directory name; the other skill's "
            "name is stale (rule: name-mismatch)"
        )
    else:
        survivor, absorbed = sorted(
            (entry_a, entry_b),
            key=lambda e: _completeness(e, skills_root),
            reverse=True,
        )
        survival_reason = (
            "both `name:` values match (or neither does); the more complete "
            "body wins (file count, then description length)"
        )

    source = skills_root / absorbed.path
    dest = skills_root / survivor.path
    moves = _asset_moves(source, dest)

    #: Every catalog row that names the absorbed path is stale the moment
    #: the folder disappears; the plan lists them rather than rewriting them.
    rewrites: list[dict[str, str]] = [
        {
            "kind": "catalog-row",
            "from": f"skills/CATALOG.md row '{absorbed.skill}' at {absorbed.path}",
            "to": f"{survivor.path} (or deletion — the survivor's row already exists)",
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

    absorbed_dir = relpath(source, skills_root)
    survivor_dir = relpath(dest, skills_root)

    return {
        "survivor": survivor_dir,
        "absorbed": absorbed_dir,
        "survival_reason": survival_reason,
        "moves": [(relpath(Path(src), skills_root), relpath(Path(dst), skills_root)) for src, dst in moves],
        "rewrites": rewrites,
        "category_after": survivor.category,
        "empty_category_after": (
            _category_left_empty(skills_root, absorbed) if survivor.category != absorbed.category else None
        ),
    }


def _references_to(skills_root: Path, path: str) -> list[str]:
    """Files under the skills root that mention an absorbed path or skill name.

    The scan is deliberately shallow: it reads the markdown whose
    ``references/``/body might link the absorbed skill, skipping the
    generated catalog (already accounted for) and binary-looking files.
    """
    skill_name = path.split("/")[-1]
    mentions: list[str] = []

    for md in sorted(skills_root.rglob("*.md")):
        if md.name == "CATALOG.md":
            continue

        rel = md.relative_to(skills_root).as_posix()
        if rel.startswith("_archive/"):
            continue
        if rel.split("/")[0] in {"_archive"}:
            continue

        try:
            text = md.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue

        if path in text or f"/{skill_name}" in text or f"]{skill_name}]" in text:
            mentions.append(rel)

    return mentions


def _category_left_empty(skills_root: Path, absorbed: model.SkillEntry) -> str | None:
    """The absorbed skill's category if removing it empties the category."""
    folder = skills_root / absorbed.category
    remaining = [
        child
        for child in sorted(folder.iterdir())
        if child.is_dir() and (child / "SKILL.md").exists() and child.name != absorbed.skill
    ]
    return absorbed.category if not remaining else None


def render_merge_plan(plan: dict[str, object]) -> list[str]:
    """Render a merge plan as the readable markdown report ``prune-skills`` consumes.

    Deterministic and stable across runs on the same tree: the plan is the
    contract between planning and execution, so its output is keyed by
    field, not by insertion whims.
    """
    lines = [
        "# Merge plan",
        "",
        f"- Survivor: `{plan['survivor']}`",
        f"- Absorbed: `{plan['absorbed']}`",
        f"- Survival: {plan['survival_reason']}",
        "",
    ]

    moves = plan["moves"]
    if moves:
        lines.append("## Moves")
        lines.append("")
        for source, dest in moves:
            lines.append(f"- `{source}` -> `{dest}`")
    else:
        lines.append("## Moves")
        lines.append("")
        lines.append("- (none — the absorbed skill has no references/ or scripts/ assets)")

    lines.append("")
    lines.append("## Rewrite")
    lines.append("")
    rewrites = plan["rewrites"]
    if rewrites:
        for rewrite in rewrites:
            lines.append(f"- [{rewrite['kind']}] {rewrite['from']}")
            lines.append(f"  -> {rewrite['to']}")
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("## Delete")
    lines.append("")
    lines.append(f"- `{plan['absorbed']}` — absorbed into `{plan['survivor']}`")

    lines.append("")
    lines.append("## After")
    lines.append("")
    lines.append(f"- Category: `{plan['category_after']}`")
    empty = plan["empty_category_after"]
    if empty:
        lines.append(
            f"- Empty category cleanup: delete `{empty}` and its `DESCRIPTION.md` "
            "(no skill folders remain)"
        )
    else:
        lines.append("- Empty category cleanup: (none)")

    return lines
