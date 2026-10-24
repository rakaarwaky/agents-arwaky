"""Discovery scoring and drift-fallback tests (ported from test_discover.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from modules.shared.src.skills.taxonomy_skills_authoring_vo import CatalogRow
from modules.shared.src.skills.taxonomy_skills_error import SkillsUsageError
from modules.skills.src.capabilities_skills_catalog import SkillsCatalog
from modules.skills.src.capabilities_skills_discoverer import (
    DRIFT_WARNING,
    SkillsDiscoverer,
    score_entries,
    tokenize,
)
from modules.skills.tests.support_skills import as_root, crafted_tree


def _rows() -> list[CatalogRow]:
    return [
        CatalogRow("doc-drafts", "drafts", "Drafts docs.", "drafts/doc-drafts"),
        CatalogRow("note-taker", "notes", "Takes notes.", "notes/note-taker"),
    ]


def test_tokenize_lowercases_and_drops_blanks() -> None:
    assert tokenize("  PDF   Tool ") == ["pdf", "tool"]


def test_scoring_order_and_weights() -> None:
    """Name +5, description +3, category +2, path +1; highest first."""
    scored = score_entries(_rows(), ["notes"])
    assert scored[0][1].skill == "note-taker"
    # "notes" hits the description (+3), category (+2), and path (+1);
    # it is not a substring of the name "note-taker".
    assert scored[0][0] == 3 + 2 + 1


def test_discover_returns_top_limit_matches(tmp_path: Path) -> None:
    """``limit`` caps the result set after ranking."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))
    result = SkillsDiscoverer(catalog).discover("drafts", as_root(root), 1)
    assert len(result.matches) == 1


def test_empty_query_is_a_usage_error(tmp_path: Path) -> None:
    """The legacy ``ERROR: Query is empty`` stays exit 2."""
    root = crafted_tree(tmp_path)
    with pytest.raises(SkillsUsageError) as failure:
        SkillsDiscoverer(SkillsCatalog()).discover("   ", as_root(root), 20)
    assert str(failure.value) == "Query is empty"
    assert failure.value.exit_code == 2


def test_discover_reads_the_catalog(tmp_path: Path) -> None:
    """A fresh catalog answers the query."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))

    result = SkillsDiscoverer(catalog).discover("docs", as_root(root), 20)
    assert result.warning == ""
    assert [match.skill for match in result.matches] == ["doc-drafts"]


def test_drift_falls_back_to_the_tree_with_a_loud_warning(tmp_path: Path) -> None:
    """A drifted catalog warns and answers from a live tree scan (exit 0)."""
    root = crafted_tree(tmp_path)

    result = SkillsDiscoverer(SkillsCatalog()).discover("docs", as_root(root), 20)

    assert result.warning == DRIFT_WARNING
    assert "Catalog missing" in result.warning_detail
    assert [match.skill for match in result.matches] == ["doc-drafts"]


def test_no_match_returns_an_empty_result(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    SkillsCatalog().rebuild(as_root(root))
    result = SkillsDiscoverer(SkillsCatalog()).discover(
        "definitely-not-a-real-skill-term", as_root(root), 20
    )
    assert result.matches == ()
