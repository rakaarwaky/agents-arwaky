"""Catalog rendering and drift-gate tests (ported from test_catalog.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.shared.src.skills.taxonomy_skills_error import CatalogDrift
from modules.skills.src.capabilities_skills_catalog import SkillsCatalog
from modules.skills.tests.support_skills import as_root, crafted_tree


def test_rebuild_writes_the_tracked_header_and_rows(tmp_path: Path) -> None:
    """A rebuild emits the documented header and one row per skill."""
    root = crafted_tree(tmp_path)
    report = SkillsCatalog().rebuild(as_root(root))

    assert report.path == root / "CATALOG.md"
    assert report.skills == 2
    assert report.categories == 2

    text = report.path.read_text(encoding="utf-8")
    assert text.startswith("# Skills Catalog\n")
    assert "Rebuild with `aa skills catalog`" in text
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
