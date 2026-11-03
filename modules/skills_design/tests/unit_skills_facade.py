"""Composition-root tests: one per authoring facade wrapper."""

from __future__ import annotations

from pathlib import Path

from modules.skills_design.src.root_skills_container import SkillsFacade
from modules.skills_design.tests.fixture_skills import crafted_tree


def _facade(root: Path) -> SkillsFacade:
    return SkillsFacade(default_root=root)


def test_facade_lint(tmp_path: Path) -> None:
    result = _facade(crafted_tree(tmp_path)).lint()
    assert result.lint_report is not None
    assert result.lint_report.issue_count == 1


def test_facade_catalog_rebuild_and_check(tmp_path: Path) -> None:
    facade = _facade(crafted_tree(tmp_path))
    rebuilt = facade.catalog_rebuild()
    assert rebuilt.catalog is not None
    assert rebuilt.catalog.skills == 2

    checked = facade.catalog_check()
    assert checked.check is not None
    assert checked.check.in_sync


def test_facade_discover(tmp_path: Path) -> None:
    facade = _facade(crafted_tree(tmp_path))
    facade.catalog_rebuild()
    result = facade.discover("docs")
    assert [match.skill for match in result.matches] == ["doc-drafts"]


def test_facade_lint_weed_lines(tmp_path: Path) -> None:
    result = _facade(crafted_tree(tmp_path)).lint()
    assert result.lint_report is not None
    assert result.lint_report.weed_lines == ()


def test_facade_move_and_archive(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    facade = _facade(root)

    moved = facade.move("drafts/doc-drafts", "notes", apply=True)
    assert moved.outcome is not None

    archived = facade.archive("notes/note-taker", apply=True)
    assert archived.outcome is not None
    assert (root / "_archive" / "notes" / "note-taker").exists()


def test_facade_create_category(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    result = _facade(root).create_category("beta-cat", "Second", apply=True)
    assert result.new_category is not None
    assert result.new_category.created
    assert (root / "beta-cat" / "DESCRIPTION.md").exists()
