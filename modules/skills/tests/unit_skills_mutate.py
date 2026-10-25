"""Mutation safety and parity tests (dry-run, containment, typed errors)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from modules.shared.src.skills.taxonomy_skills_error import (
    MutationConflictError,
    SkillNotFoundError,
    SkillsUsageError,
)
from modules.skills.src.capabilities_skills_mutator import SkillsMutator
from modules.skills.tests.fixture_skills import as_root, crafted_tree


def test_repair_plan_is_pure_and_names_the_work(tmp_path: Path) -> None:
    """Planning writes nothing; the step lines match the legacy report."""
    root = crafted_tree(tmp_path)
    plan = SkillsMutator().plan_repair(as_root(root))

    assert plan.kind == "repair"
    assert plan.lines == ("Fixed name in doc-drafts/SKILL.md",)
    assert (root / "drafts" / "doc-drafts" / "SKILL.md").read_text(
        encoding="utf-8"
    ).startswith("---\nname: wrong-name")


def test_mutating_commands_default_to_dry_run(tmp_path: Path) -> None:
    """§5.5: no apply means no write, for every mutating verb."""
    mutator = SkillsMutator()
    root = crafted_tree(tmp_path)
    before = (root / "drafts" / "DESCRIPTION.md").read_text(encoding="utf-8")

    mutator.plan_repair(as_root(root))
    mutator.plan_move("drafts/doc-drafts", "notes", as_root(root))
    mutator.plan_archive("drafts/doc-drafts", as_root(root))
    mutator.plan_new_category("beta-cat", "Second category", as_root(root), False)

    assert not (root / "beta-cat").exists(), "new-category created a directory in dry-run"
    assert not (root / "_archive").exists(), "archive wrote in dry-run"
    assert (root / "drafts" / "doc-drafts").exists(), "move wrote in dry-run"
    assert (root / "drafts" / "DESCRIPTION.md").read_text(encoding="utf-8") == before


def test_repair_apply_rewrites_only_on_apply(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    mutator = SkillsMutator()
    plan = mutator.plan_repair(as_root(root))
    outcome = mutator.apply(plan)

    assert outcome.applied == ("Fixed name in drafts/doc-drafts/SKILL.md",)
    text = (root / "drafts" / "doc-drafts" / "SKILL.md").read_text(encoding="utf-8")
    assert "name: doc-drafts" in text


def test_move_plan_then_apply(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    mutator = SkillsMutator()
    plan = mutator.plan_move("drafts/doc-drafts", "notes", as_root(root))

    assert plan.source == (root / "drafts" / "doc-drafts").resolve()
    assert plan.destination == root / "notes" / "doc-drafts"
    assert (root / "drafts" / "doc-drafts").exists(), "plan must not write"

    mutator.apply(plan)
    assert (root / "notes" / "doc-drafts" / "SKILL.md").exists()
    assert not (root / "drafts" / "doc-drafts").exists()


def test_move_into_the_same_category_is_a_no_op(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    plan = SkillsMutator().plan_move("drafts/doc-drafts", "drafts", as_root(root))
    assert plan.already_in_category


def test_move_conflicts_fail_typed(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    (root / "notes" / "doc-drafts").mkdir()
    with pytest.raises(MutationConflictError):
        SkillsMutator().plan_move("drafts/doc-drafts", "notes", as_root(root))


def test_unknown_skill_is_a_usage_error(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    with pytest.raises(SkillNotFoundError) as failure:
        SkillsMutator().plan_move("nope", "notes", as_root(root))
    assert str(failure.value).startswith("Could not find skill directory with SKILL.md")
    assert failure.value.exit_code == 2


def test_dry_run_leaves_a_clean_worktree(tmp_path: Path) -> None:
    """Hard constraint: a plan-only pass leaves the tree byte-identical."""
    mutator = SkillsMutator()
    root = crafted_tree(tmp_path)
    snapshot = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

    mutator.plan_repair(as_root(root))
    mutator.plan_move("drafts/doc-drafts", "notes", as_root(root))
    mutator.plan_archive("drafts/doc-drafts", as_root(root))
    mutator.plan_new_category("zz-dry-run-only", "Never created", as_root(root), False)

    assert sorted(
        path.relative_to(root).as_posix() for path in root.rglob("*")
    ) == snapshot, "a plan modified the tree"


def test_exit_code_2_nonexistent_skill_is_a_usage_error(tmp_path: Path) -> None:
    """Legacy contract: an unknown skill ref is caller input, exit 2."""
    mutator = SkillsMutator()
    root = crafted_tree(tmp_path)
    for verb in (
        ("plan_move", ("nonexistent-skill", "notes")),
        ("plan_archive", ("nonexistent-skill",)),
    ):
        with pytest.raises(SkillNotFoundError) as failure:
            getattr(mutator, verb[0])(*verb[1], as_root(root))
        assert failure.value.exit_code == 2
        assert "nonexistent-skill" in str(failure.value)


def test_archive_apply_moves_and_renames(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    mutator = SkillsMutator()
    plan = mutator.plan_archive("notes/note-taker", as_root(root))
    mutator.apply(plan)

    archived = root / "_archive" / "notes" / "note-taker"
    assert (archived / "SKILL.md.archived").exists()
    assert not (archived / "SKILL.md").exists()
    assert not (root / "notes" / "note-taker").exists()


def test_new_category_plan_and_apply(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    mutator = SkillsMutator()
    plan = mutator.plan_new_category("beta-cat", "Second category", as_root(root), False)

    assert plan.will_write
    assert not plan.directory.exists()

    assert mutator.apply_new_category(plan)
    assert "Second category" in (root / "beta-cat" / "DESCRIPTION.md").read_text()


def test_new_category_keeps_an_existing_description_without_force(
    tmp_path: Path,
) -> None:
    root = crafted_tree(tmp_path)
    mutator = SkillsMutator()
    (root / "beta-cat").mkdir()
    (root / "beta-cat" / "DESCRIPTION.md").write_text("---\ndescription: old\n---\n")

    plan = mutator.plan_new_category("beta-cat", "new", as_root(root), False)
    assert not plan.will_write
    assert not mutator.apply_new_category(plan)
    assert "old" in (root / "beta-cat" / "DESCRIPTION.md").read_text()


def test_category_name_is_validated(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    with pytest.raises(SkillsUsageError):
        SkillsMutator().plan_new_category("../escape", "x", as_root(root), False)


def test_symlinked_target_category_cannot_escape_the_root(tmp_path: Path) -> None:
    """S1: a destination that resolves outside the root fails closed."""
    root = crafted_tree(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(SkillsUsageError) as failure:
        SkillsMutator().plan_move("drafts/doc-drafts", "linked", as_root(root))
    assert "outside the skills root" in str(failure.value)


def test_symlink_created_after_plan_fails_at_apply(tmp_path: Path) -> None:
    """S1: apply re-checks containment, so a race fails closed."""
    root = crafted_tree(tmp_path)
    mutator = SkillsMutator()
    plan = mutator.plan_archive("notes/note-taker", as_root(root))

    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "_archive").symlink_to(outside, target_is_directory=True)

    with pytest.raises(SkillsUsageError) as failure:
        mutator.apply(plan)
    assert "outside the skills root" in str(failure.value)
    assert (root / "notes" / "note-taker").exists()


def test_weed_report_exempts_asset_containers(tmp_path: Path) -> None:
    """A declared DM2 asset container is never reported as empty."""
    root = crafted_tree(tmp_path)
    (root / "shared").mkdir()
    (root / "shared" / "ASSETS.md").write_text(
        "---\nkind: assets\ndescription: shared assets\n---\n", encoding="utf-8"
    )

    plan = SkillsMutator().plan_weed(as_root(root))
    assert plan.lines == ()


def test_weed_reports_duplicates(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    (root / "notes" / "doc-drafts").mkdir()
    (root / "notes" / "doc-drafts" / "SKILL.md").write_text(
        "---\nname: doc-drafts\ndescription: Drafts docs.\n---\n", encoding="utf-8"
    )

    plan = SkillsMutator().plan_weed(as_root(root))
    assert any("duplicate-skill-name" in line for line in plan.lines)
    assert any("duplicate-description" in line for line in plan.lines)


def test_parse_frontmatter_falls_back_without_pyyaml(tmp_path: Path, monkeypatch) -> None:
    """S8: the optional-PyYAML fallback keeps parsing the pack."""
    import modules.shared.src.common.utility_skills_tree as tree

    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(
        '---\nname: alpha\ndescription: "Does alpha."\n---\n\n# alpha\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(tree, "yaml", None)
    frontmatter = tree.parse_frontmatter(skill_md)
    assert frontmatter["name"] == "alpha"
    assert frontmatter["description"] == "Does alpha."


def test_os_walk_does_not_follow_symlinked_directories(tmp_path: Path) -> None:
    """S6: a symlink loop cannot hang or duplicate a recursive scan."""
    from modules.shared.src.common.utility_skills_tree import iter_files

    root = tmp_path / "root"
    (root / "a").mkdir(parents=True)
    (root / "a" / "file.txt").write_text("x", encoding="utf-8")
    if os.name == "posix":
        (root / "loop").symlink_to(root, target_is_directory=True)
        found = {path.relative_to(root).as_posix() for path in iter_files(root)}
        assert found == {"a/file.txt"}
