"""Catalog rendering and drift-gate tests (ported from test_catalog.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from shared.src.common.utility_skills_tree import category_summaries, skill_entries
from shared.src.skills_design.taxonomy_skills_error import CatalogDrift

from skills_design.src.capabilities_skills_catalog import (
    SkillsCatalog,
    render_catalog_json,
)
from skills_design.tests.fixture_skills import as_root, crafted_tree


def test_rebuild_writes_the_tracked_header_and_rows(tmp_path: Path) -> None:
    """A rebuild emits the documented header and one row per skill."""
    root = crafted_tree(tmp_path)
    report = SkillsCatalog().rebuild(as_root(root))

    assert report.path == root / "CATALOG.md"
    assert report.skills == 2
    assert report.categories == 2

    text = report.path.read_text(encoding="utf-8")
    assert text.startswith("# Skills Catalog\n")
    assert "Rebuild with `sdc skills catalog`" in text
    assert "| doc-drafts | drafts | Drafts docs. | drafts/doc-drafts |" in text


def test_check_is_in_sync_immediately_after_rebuild(tmp_path: Path) -> None:
    """The drift gate passes on the artifact a rebuild just wrote."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))

    result = catalog.check(as_root(root))
    assert result.in_sync
    assert result.diff_lines == ()
    assert result.message == f"Catalog in sync: {root / 'CATALOG.md'}"


def test_check_detects_a_missing_catalog(tmp_path: Path) -> None:
    """A missing catalog is drift (exit 3), not a usage error."""
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


def test_check_fails_closed_on_a_lossy_cell(tmp_path: Path) -> None:
    """A crafted ``&#124;`` description cannot read as in sync."""
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "DESCRIPTION.md").write_text(
        "---\ndescription: Crafted cells\n---\n", encoding="utf-8"
    )
    (root / "cat" / "corrupt").mkdir()
    (root / "cat" / "corrupt" / "SKILL.md").write_text(
        "---\nname: corrupt\ndescription: bad cell &#124; here\n---\n",
        encoding="utf-8",
    )

    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))
    result = catalog.check(as_root(root))

    assert not result.in_sync
    assert "do not round-trip" in result.message
    assert result.diff_lines


def test_load_rows_reads_a_fresh_catalog(tmp_path: Path) -> None:
    """Rows parse back into the source tree's own values."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))

    rows = catalog.load_rows(as_root(root))
    assert [(row.skill, row.category) for row in rows] == [
        ("doc-drafts", "drafts"),
        ("note-taker", "notes"),
    ]
    assert rows[0].as_dict()["description"] == "Drafts docs."


def test_load_rows_fails_closed_on_missing_catalog(tmp_path: Path) -> None:
    """The read path raises instead of rebuilding silently."""
    with pytest.raises(CatalogDrift) as failure:
        SkillsCatalog().load_rows(as_root(crafted_tree(tmp_path)))
    assert "Catalog missing" in str(failure.value)


def test_load_rows_fails_closed_on_stale_rows(tmp_path: Path) -> None:
    """A stale tracked row is drift, never an answer."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))

    (root / "notes" / "note-taker" / "SKILL.md").write_text(
        "---\nname: note-taker\ndescription: New text.\n---\n", encoding="utf-8"
    )

    with pytest.raises(CatalogDrift) as failure:
        catalog.load_rows(as_root(root))
    assert "drift detected" in str(failure.value)


def test_crafted_pipe_row_round_trips(tmp_path: Path) -> None:
    """A legitimate ``|`` in a description escapes and parses back losslessly."""
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    (root / "cat" / "DESCRIPTION.md").write_text(
        "---\ndescription: Cats\n---\n", encoding="utf-8"
    )
    (root / "cat" / "piped").mkdir()
    (root / "cat" / "piped" / "SKILL.md").write_text(
        "---\nname: piped\ndescription: a|b\n---\n", encoding="utf-8"
    )

    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))
    rows = catalog.load_rows(as_root(root))
    assert rows[0].description == "a|b"
    assert catalog.check(as_root(root)).in_sync


def test_render_catalog_json_emits_all_four_fields(tmp_path: Path) -> None:
    """render_catalog_json emits exactly name, description, when_to_use,
    category per skill (task 3)."""
    root = crafted_tree(tmp_path)
    entries = skill_entries(root)
    categories = category_summaries(entries, root)
    text = render_catalog_json(entries, categories)
    data = json.loads(text)
    assert set(data.keys()) == {"skills"}
    skills = data["skills"]
    assert len(skills) == 2
    for s in skills:
        assert set(s.keys()) == {"name", "description", "when_to_use", "category"}


def test_rebuild_writes_catalog_json_with_all_fields(tmp_path: Path) -> None:
    """Rebuild writes catalog.json with name, description, when_to_use,
    category (task 4)."""
    root = crafted_tree(tmp_path)
    SkillsCatalog().rebuild(as_root(root))
    json_path = root / "catalog.json"
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert set(data.keys()) == {"skills"}
    skills = data["skills"]
    assert len(skills) == 2
    for s in skills:
        assert set(s.keys()) == {"name", "description", "when_to_use", "category"}


def test_check_detects_catalog_json_drift(tmp_path: Path) -> None:
    """A hand-edited catalog.json is drift, fail-closed (task 5)."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))
    (root / "catalog.json").write_text(
        '{"skills": [{"name":"x","description":"d","when_to_use":"w","category":"c"}]}',
        encoding="utf-8",
    )
    result = catalog.check(as_root(root))
    assert not result.in_sync
    assert "Catalog JSON drift" in result.message
