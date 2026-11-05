"""Mutation safety and parity tests (dry-run, containment, typed errors)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from shared.src.common.utility_skills_mutation import plan_repair, plan_weed
from shared.src.skills_design.taxonomy_skills_error import (
    MutationConflictError,
    SkillNotFoundError,
    SkillsUsageError,
)
from shared.src.skills_design.taxonomy_skills_request import SkillsOp, SkillsRequest

from skills_design.src.agent_skills_orchestrator import SkillsAgent
from skills_design.src.capabilities_skills_archiver import SkillsArchiver
from skills_design.src.capabilities_skills_catalog import SkillsCatalog
from skills_design.src.capabilities_skills_creator import SkillsCreator
from skills_design.src.capabilities_skills_mover import SkillsMover
from skills_design.tests.fixture_skills import as_root, crafted_tree


def test_repair_plan_is_pure_and_names_the_work(tmp_path: Path) -> None:
    """Planning writes nothing; the step lines match the legacy report."""
    root = crafted_tree(tmp_path)
    plan = plan_repair(as_root(root))

    assert plan.kind == "repair"
    assert plan.lines == ("Fixed name in doc-drafts/SKILL.md",)
    assert (root / "drafts" / "doc-drafts" / "SKILL.md").read_text(
        encoding="utf-8"
    ).startswith("---\nname: wrong-name")


def test_mutating_commands_default_to_dry_run(tmp_path: Path) -> None:
    """§5.5: no apply means no write, for every mutating verb."""
    mover = SkillsMover()
    archiver = SkillsArchiver()
    creator = SkillsCreator()
    root = crafted_tree(tmp_path)
    before = (root / "drafts" / "DESCRIPTION.md").read_text(encoding="utf-8")

    mover.plan_move("drafts/doc-drafts", "notes", as_root(root))
    archiver.plan_archive("drafts/doc-drafts", as_root(root))
    creator.create_category("beta-cat", "Second category", as_root(root), False, False)

    assert not (root / "beta-cat").exists(), "new-category created a directory in dry-run"
    assert not (root / "_archive").exists(), "archive wrote in dry-run"
    assert (root / "drafts" / "doc-drafts").exists(), "move wrote in dry-run"
    assert (root / "drafts" / "DESCRIPTION.md").read_text(encoding="utf-8") == before


def test_repair_plan_is_pure_and_matches_the_legacy_report(tmp_path: Path) -> None:
    """Repair is pure planning now: the step lines match the legacy report
    and planning writes nothing to the tree."""
    root = crafted_tree(tmp_path)
    snapshot = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))

    plan = plan_repair(as_root(root))

    assert plan.kind == "repair"
    assert plan.lines == ("Fixed name in doc-drafts/SKILL.md",)
    assert sorted(p.relative_to(root).as_posix() for p in root.rglob("*")) == snapshot


def test_move_plan_then_apply(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    mover = SkillsMover()
    plan = mover.plan_move("drafts/doc-drafts", "notes", as_root(root))

    assert plan.source == (root / "drafts" / "doc-drafts").resolve()
    assert plan.destination == root / "notes" / "doc-drafts"
    assert (root / "drafts" / "doc-drafts").exists(), "plan must not write"

    mover.apply_move(plan)
    assert (root / "notes" / "doc-drafts" / "SKILL.md").exists()
    assert not (root / "drafts" / "doc-drafts").exists()


def test_move_into_the_same_category_is_a_no_op(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    plan = SkillsMover().plan_move("drafts/doc-drafts", "drafts", as_root(root))
    assert plan.already_in_category


def test_move_conflicts_fail_typed(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    (root / "notes" / "doc-drafts").mkdir()
    with pytest.raises(MutationConflictError):
        SkillsMover().plan_move("drafts/doc-drafts", "notes", as_root(root))


def test_unknown_skill_is_a_usage_error(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    with pytest.raises(SkillNotFoundError) as failure:
        SkillsMover().plan_move("nope", "notes", as_root(root))
    assert str(failure.value).startswith("Could not find skill directory with SKILL.md")
    assert failure.value.exit_code == 2


def test_dry_run_leaves_a_clean_worktree(tmp_path: Path) -> None:
    """Hard constraint: a plan-only pass leaves the tree byte-identical."""
    mover = SkillsMover()
    archiver = SkillsArchiver()
    creator = SkillsCreator()
    root = crafted_tree(tmp_path)
    snapshot = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))

    mover.plan_move("drafts/doc-drafts", "notes", as_root(root))
    archiver.plan_archive("drafts/doc-drafts", as_root(root))
    creator.create_category("zz-dry-run-only", "Never created", as_root(root), False, False)

    assert sorted(
        path.relative_to(root).as_posix() for path in root.rglob("*")
    ) == snapshot, "a plan modified the tree"


def test_exit_code_2_nonexistent_skill_is_a_usage_error(tmp_path: Path) -> None:
    """Legacy contract: an unknown skill ref is caller input, exit 2."""
    mover = SkillsMover()
    archiver = SkillsArchiver()
    root = crafted_tree(tmp_path)
    for capability, method, args in (
        (mover, "plan_move", ("nonexistent-skill", "notes")),
        (archiver, "plan_archive", ("nonexistent-skill",)),
    ):
        with pytest.raises(SkillNotFoundError) as failure:
            getattr(capability, method)(*args, as_root(root))
        assert failure.value.exit_code == 2
        assert "nonexistent-skill" in str(failure.value)


def test_archive_apply_moves_and_renames(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    archiver = SkillsArchiver()
    plan = archiver.plan_archive("notes/note-taker", as_root(root))
    archiver.apply_archive(plan)

    archived = root / "_archive" / "notes" / "note-taker"
    assert (archived / "SKILL.md.archived").exists()
    assert not (archived / "SKILL.md").exists()
    assert not (root / "notes" / "note-taker").exists()


def test_new_category_plan_and_apply(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    creator = SkillsCreator()
    plan = creator.create_category("beta-cat", "Second category", as_root(root), False, False)

    assert plan.will_write
    assert not plan.directory.exists()

    created = creator.create_category("beta-cat", "Second category", as_root(root), False, True)
    assert created.created
    assert "Second category" in (root / "beta-cat" / "DESCRIPTION.md").read_text()


def test_new_category_keeps_an_existing_description_without_force(
    tmp_path: Path,
) -> None:
    root = crafted_tree(tmp_path)
    creator = SkillsCreator()
    (root / "beta-cat").mkdir()
    (root / "beta-cat" / "DESCRIPTION.md").write_text("---\ndescription: old\n---\n")

    plan = creator.create_category("beta-cat", "new", as_root(root), False, False)
    assert not plan.will_write


def test_category_name_is_validated(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    with pytest.raises(SkillsUsageError):
        SkillsCreator().create_category("../escape", "x", as_root(root), False, False)


def test_symlinked_target_category_cannot_escape_the_root(tmp_path: Path) -> None:
    """S1: a destination that resolves outside the root fails closed."""
    root = crafted_tree(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(SkillsUsageError) as failure:
        SkillsMover().plan_move("drafts/doc-drafts", "linked", as_root(root))
    assert "outside the skills root" in str(failure.value)


def test_symlink_created_after_plan_fails_at_apply(tmp_path: Path) -> None:
    """S1: apply re-checks containment, so a race fails closed."""
    root = crafted_tree(tmp_path)
    archiver = SkillsArchiver()
    plan = archiver.plan_archive("notes/note-taker", as_root(root))

    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "_archive").symlink_to(outside, target_is_directory=True)

    with pytest.raises(SkillsUsageError) as failure:
        archiver.apply_archive(plan)
    assert "outside the skills root" in str(failure.value)
    assert (root / "notes" / "note-taker").exists()


def test_weed_report_exempts_asset_containers(tmp_path: Path) -> None:
    """A declared DM2 asset container is never reported as empty."""
    root = crafted_tree(tmp_path)
    (root / "shared").mkdir()
    (root / "shared" / "ASSETS.md").write_text(
        "---\nkind: assets\ndescription: shared assets\n---\n", encoding="utf-8"
    )

    plan = plan_weed(as_root(root))
    assert plan.lines == ()


def test_weed_reports_duplicates(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    (root / "notes" / "doc-drafts").mkdir()
    (root / "notes" / "doc-drafts" / "SKILL.md").write_text(
        "---\nname: doc-drafts\ndescription: Drafts docs.\n---\n", encoding="utf-8"
    )

    plan = plan_weed(as_root(root))
    assert any("duplicate-skill-name" in line for line in plan.lines)
    assert any("duplicate-description" in line for line in plan.lines)


def test_parse_frontmatter_falls_back_without_pyyaml(tmp_path: Path, monkeypatch) -> None:
    """S8: the optional-PyYAML fallback keeps parsing the pack."""
    import shared.src.common.utility_skills_tree as tree

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
    from shared.src.common.utility_skills_tree import iter_files

    root = tmp_path / "root"
    (root / "a").mkdir(parents=True)
    (root / "a" / "file.txt").write_text("x", encoding="utf-8")
    if os.name == "posix":
        (root / "loop").symlink_to(root, target_is_directory=True)
        found = {path.relative_to(root).as_posix() for path in iter_files(root)}
        assert found == {"a/file.txt"}


def _create_agent(root: Path) -> SkillsAgent:
    """Build a SkillsAgent wired to *root* with the create pipeline."""
    catalog = SkillsCatalog()
    return SkillsAgent(
        None,  # lister unused
        None,  # reader unused
        catalog=catalog,
        creator=SkillsCreator(),
        default_root=root,
    )


def test_create_dry_run_writes_nothing(tmp_path: Path) -> None:
    """§5.5: plan-only create leaves the tree untouched."""
    agent = _create_agent(tmp_path)
    request = SkillsRequest(
        op=SkillsOp.CREATE,
        query="doc-helper",
        description="Helps with docs",
        flags={
            "category": "automation",
            "when_to_use": "Use when writing documentation",
            "argument_hint": "<path>",
            "body": "# Doc Helper",
        },
        root=tmp_path,
        apply=False,
    )
    result = agent.execute(request)
    assert result.ok
    assert not result.create_plan.already_exists
    assert not (tmp_path / "automation" / "doc-helper" / "SKILL.md").exists()


def test_create_apply_writes_skill_md_and_rebuilds_catalog(tmp_path: Path) -> None:
    """Applying creates SKILL.md and rebuilds catalog.json."""
    agent = _create_agent(tmp_path)
    (tmp_path / "catalog.json").write_text("{}", encoding="utf-8")
    request = SkillsRequest(
        op=SkillsOp.CREATE,
        query="doc-helper",
        description="Helps with docs",
        flags={
            "category": "automation",
            "when_to_use": "Use when writing documentation",
            "argument_hint": "<path>",
            "body": "# Doc Helper\n",
        },
        root=tmp_path,
        apply=True,
    )
    result = agent.execute(request)
    assert result.ok
    skill_md = tmp_path / "automation" / "doc-helper" / "SKILL.md"
    assert skill_md.exists()
    text = skill_md.read_text(encoding="utf-8")
    assert text.startswith("---\nname: doc-helper\n")
    assert 'when-to-use: "Use when writing documentation"' in text
    assert "argument-hint: <path>" in text
    assert "# Doc Helper" in text
    assert result.catalog is not None, "catalog should be rebuilt after apply"
    assert (tmp_path / "catalog.json").exists()


def test_create_already_exists_is_a_no_op(tmp_path: Path) -> None:
    """Re-creating an existing skill writes nothing."""
    (tmp_path / "automation" / "doc-helper").mkdir(parents=True)
    (tmp_path / "automation" / "doc-helper" / "SKILL.md").write_text(
        "---\nname: doc-helper\ndescription: old\nwhen-to-use: \"old\"\nargument-hint: <old>\n---\n",
        encoding="utf-8",
    )
    agent = _create_agent(tmp_path)
    request = SkillsRequest(
        op=SkillsOp.CREATE,
        query="doc-helper",
        description="Helps with docs",
        flags={
            "category": "automation",
            "when_to_use": "Use when writing documentation",
            "argument_hint": "<path>",
            "body": "# Doc Helper\n",
        },
        root=tmp_path,
        apply=True,
    )
    result = agent.execute(request)
    assert result.ok
    assert result.create_plan.already_exists
    text = (tmp_path / "automation" / "doc-helper" / "SKILL.md").read_text(encoding="utf-8")
    assert "description: old" in text, "existing skill file must not be overwritten"


def test_create_without_category_is_a_usage_error(tmp_path: Path) -> None:
    agent = _create_agent(tmp_path)
    request = SkillsRequest(
        op=SkillsOp.CREATE,
        query="doc-helper",
        description="Helps with docs",
        flags={
            "category": "",
            "when_to_use": "",
            "argument_hint": "",
            "body": "",
        },
        root=tmp_path,
        apply=True,
    )
    result = agent.execute(request)
    assert not result.ok
    assert result.exit_code == 2
