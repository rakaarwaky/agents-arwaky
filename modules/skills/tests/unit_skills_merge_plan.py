"""Read-only merge-plan tests (ported from test_cli.py merge cases)."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.shared.src.skills.taxonomy_skills_error import (
    MutationConflictError,
    SkillNotFoundError,
    SkillsUsageError,
)
from modules.skills.src.capabilities_skills_merge_planner import (
    SkillsMergePlanner,
    parse_ref,
)
from modules.skills.tests.support_skills import as_root


def _merge_tree(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "DESCRIPTION.md").write_text(
        "---\ndescription: Cat\n---\n", encoding="utf-8"
    )
    (root / "cat" / "stale-name").mkdir()
    (root / "cat" / "stale-name" / "SKILL.md").write_text(
        "---\nname: something-else\ndescription: Same job.\n---\n\n# stale\n",
        encoding="utf-8",
    )
    (root / "cat" / "aligned-name").mkdir()
    (root / "cat" / "aligned-name" / "SKILL.md").write_text(
        "---\nname: aligned-name\ndescription: Same job.\n---\n\n# aligned\n",
        encoding="utf-8",
    )
    return root


def test_parse_ref_rejects_a_bare_name() -> None:
    with pytest.raises(SkillsUsageError) as failure:
        parse_ref("qwen-web")
    assert "must be 'category/skill'" in str(failure.value)


def test_survivor_is_the_skill_whose_name_matches(tmp_path: Path) -> None:
    """The aligned name survives; the stale frontmatter is absorbed."""
    root = _merge_tree(tmp_path)
    plan = SkillsMergePlanner().plan(
        "cat/stale-name", "cat/aligned-name", as_root(root)
    )

    assert plan.survivor == "cat/aligned-name"
    assert plan.absorbed == "cat/stale-name"
    assert "name-mismatch" in plan.survival_reason
    assert plan.category_after == "cat"
    assert plan.empty_category_after is None


def test_plan_lists_moves_and_rewrites(tmp_path: Path) -> None:
    root = _merge_tree(tmp_path)
    (root / "cat" / "stale-name" / "references").mkdir()
    (root / "cat" / "stale-name" / "references" / "notes.md").write_text(
        "stale-name details", encoding="utf-8"
    )

    plan = SkillsMergePlanner().plan(
        "cat/stale-name", "cat/aligned-name", as_root(root)
    )

    assert ("cat/stale-name/references/notes.md", "cat/aligned-name/references/notes.md") in plan.moves
    kinds = {rewrite["kind"] for rewrite in plan.rewrites}
    assert "catalog-row" in kinds


def test_conflicts_fail_typed(tmp_path: Path) -> None:
    root = _merge_tree(tmp_path)
    (root / "cat" / "stale-name" / "extra.md").write_text("x", encoding="utf-8")
    (root / "cat" / "aligned-name" / "extra.md").write_text("y", encoding="utf-8")

    with pytest.raises(MutationConflictError):
        SkillsMergePlanner().plan("cat/stale-name", "cat/aligned-name", as_root(root))


def test_missing_skill_fails_typed(tmp_path: Path) -> None:
    root = _merge_tree(tmp_path)
    with pytest.raises(SkillNotFoundError):
        SkillsMergePlanner().plan("cat/nope", "cat/aligned-name", as_root(root))


def test_render_is_the_readable_plan(tmp_path: Path) -> None:
    root = _merge_tree(tmp_path)
    planner = SkillsMergePlanner()
    plan = planner.plan("cat/stale-name", "cat/aligned-name", as_root(root))
    lines = planner.render(plan)

    assert lines[0] == "# Merge plan"
    assert "- Survivor: `cat/aligned-name`" in lines
    assert "## Moves" in lines
    assert "## Rewrite" in lines
    assert "## Delete" in lines
    assert "## After" in lines
