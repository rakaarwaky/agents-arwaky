"""Catalog rendering and drift-gate tests (catalog.json artifact)."""

from __future__ import annotations

import json
from pathlib import Path

from shared.src.common.utility_skills_tree import category_summaries, skill_entries

from skills_design.src.capabilities_skills_catalog import SkillsCatalog
from skills_design.tests.fixture_skills import as_root, crafted_tree


def test_rebuild_writes_catalog_json_with_all_fields(tmp_path: Path) -> None:
    """A rebuild emits catalog.json with one object per skill (name, description, when_to_use, category)."""
    root = crafted_tree(tmp_path)
    report = SkillsCatalog().rebuild(as_root(root))

    assert report.path == root / "catalog.json"
    assert report.skills == 2
    assert report.categories == 2

    data = json.loads(report.path.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"skills"}
    skills = data["skills"]
    assert len(skills) == 2
    for s in skills:
        assert set(s.keys()) == {"name", "description", "when_to_use", "category"}

    names = [s["name"] for s in skills]
    assert "doc-drafts" in names
    assert "note-taker" in names


def test_render_catalog_json_emits_all_four_fields(tmp_path: Path) -> None:
    """render_catalog_json output contains exactly the four catalog keys."""
    from skills_design.src.capabilities_skills_catalog import render_catalog_json

    root = crafted_tree(tmp_path)
    entries = skill_entries(root)
    categories = category_summaries(entries, root)

    text = render_catalog_json(entries, categories)
    data = json.loads(text)
    assert set(data.keys()) == {"skills"}
    assert len(data["skills"]) == 2
    for s in data["skills"]:
        assert set(s.keys()) == {"name", "description", "when_to_use", "category"}


def test_check_is_in_sync_immediately_after_rebuild(tmp_path: Path) -> None:
    """The drift gate passes on the artifact a rebuild just wrote."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))

    result = catalog.check(as_root(root))
    assert result.in_sync
    assert result.diff_lines == ()
    assert result.message == f"Catalog in sync: {root / 'catalog.json'}"


def test_check_detects_a_missing_catalog(tmp_path: Path) -> None:
    """A missing catalog.json is drift (exit 3), not a usage error."""
    result = SkillsCatalog().check(as_root(crafted_tree(tmp_path)))
    assert not result.in_sync
    assert "Catalog missing" in result.message
    assert result.diff_lines == ()


def test_check_detects_stale_content_and_counts_the_diff(tmp_path: Path) -> None:
    """The drift message's diff-line count is the actual diff size."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))

    (root / "notes" / "note-taker" / "SKILL.md").write_text(
        "---\nname: note-taker\ndescription: Changed description.\n---\n",
        encoding="utf-8",
    )

    result = catalog.check(as_root(root))
    assert not result.in_sync
    assert f"({len(result.diff_lines)} diff line(s))" in result.message
    assert result.diff_lines


def test_check_detects_hand_edited_catalog_json_drift(tmp_path: Path) -> None:
    """A hand-edited catalog.json is drift (fail-closed)."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))

    (root / "catalog.json").write_text(
        '{"skills": [{"name":"x","description":"d","when_to_use":"w","category":"c"}]}',
        encoding="utf-8",
    )

    result = catalog.check(as_root(root))
    assert not result.in_sync
    assert "Catalog JSON drift" in result.message or "drift detected" in result.message


def test_read_returns_json_text_after_rebuild(tmp_path: Path) -> None:
    """read() returns the tracked catalog.json text after a rebuild."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))

    text = catalog.read(as_root(root))
    assert text == root.joinpath("catalog.json").read_text(encoding="utf-8")
    assert '"skills"' in text
