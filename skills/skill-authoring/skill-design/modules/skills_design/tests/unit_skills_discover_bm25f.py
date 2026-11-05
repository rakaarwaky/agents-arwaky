"""Tests for the BM25F discover ranker (offline, no network, no third-party deps).

Covers:
* ``tokenize_full`` — lowercasing, hyphen-split, stop-word filtering
* ``rank_bm25f``    — ranking order and zero-score exclusion
* ``map_to_legacy_score`` — float→int projection
* ``SkillsDiscover(ranker="bm25f")`` end-to-end via the catalog
* agent-level ``ranker`` flag dispatch (the agent swaps to a BM25F discoverer)
"""

from __future__ import annotations

from pathlib import Path

from skills_design.src.capabilities_skills_bm25f import (
    build_index,
    map_to_legacy_score,
    rank_bm25f,
    tokenize_full,
)
from skills_design.src.capabilities_skills_catalog import SkillsCatalog
from skills_design.src.capabilities_skills_discover import SkillsDiscover, _Row
from skills_design.tests.fixture_skills import as_root, crafted_tree

# ── Helpers ───────────────────────────────────────────────────────────

def _rows() -> list[_Row]:
    return [
        _Row("pdf-extract", "office", "Extract tables and text from PDF files.", "office/pdf-extract"),
        _Row("note-taker", "notes", "Takes notes.", "notes/note-taker"),
        _Row("doc-drafts", "drafts", "Drafts docs.", "drafts/doc-drafts"),
        _Row("csv-clean", "office", "Clean malformed and duplicate rows in CSV files.", "office/csv-clean"),
    ]


# ── tokenize_full ─────────────────────────────────────────────────────

def test_tokenize_full_lowercases_and_splits_hyphens() -> None:
    # "2" is dropped (single char < MIN_TOKEN_LEN)
    assert tokenize_full("PDF-Extract 2.0") == ["pdf", "extract"]


def test_tokenize_full_drops_stop_words() -> None:
    # "how", "to", "the", "use" are stop words; "pdf" and "tool" are not
    assert tokenize_full("how to use the pdf tool") == ["pdf", "tool"]


def test_tokenize_full_empty() -> None:
    assert tokenize_full("") == []


# ── build_index ───────────────────────────────────────────────────────

def test_build_index_avgdl() -> None:
    idx = build_index(_rows())
    # avgdl for "name" field: each row has 1–3 name tokens
    # pdf-extract → 2, note-taker → 2, doc-drafts → 2, csv-clean → 2
    assert idx.avgdl["name"] == 2.0
    # "description" field lengths vary
    assert idx.n_docs == 4


def test_build_index_df_counts() -> None:
    idx = build_index(_rows())
    # "office" appears in two rows' category fields
    assert idx.df["category"]["office"] == 2
    # "notes" appears in one row's category field
    assert idx.df["category"]["notes"] == 1


# ── rank_bm25f ────────────────────────────────────────────────────────

def test_rank_bm25f_orders_pdf_above_notes_for_pdf_query() -> None:
    scored = rank_bm25f(_rows(), ["pdf"])
    names = [row.skill for _, row in scored]
    assert names[0] == "pdf-extract", f"expected pdf-extract first, got {names}"
    # note-taker / doc-drafts / csv-clean have no "pdf" token → excluded
    assert "note-taker" not in names
    assert "doc-drafts" not in names
    assert "csv-clean" not in names


def test_rank_bm25f_csv_ranks_csv_clean_first() -> None:
    scored = rank_bm25f(_rows(), ["csv", "clean"])
    names = [row.skill for _, row in scored]
    assert names[0] == "csv-clean"


def test_rank_bm25f_zero_score_rows_excluded() -> None:
    scored = rank_bm25f(_rows(), ["nonexistent"])
    assert scored == []


def test_rank_bm25f_empty_query_returns_empty() -> None:
    assert rank_bm25f(_rows(), []) == []


def test_rank_bm25f_empty_rows_returns_empty() -> None:
    assert rank_bm25f([], ["pdf"]) == []


# ── map_to_legacy_score ──────────────────────────────────────────────

def test_map_to_legacy_score_rounds() -> None:
    assert map_to_legacy_score(0.0) == 0
    assert map_to_legacy_score(1.234) == 123
    assert map_to_legacy_score(0.004) == 0  # rounds to 0


def test_map_to_legacy_score_negative_clamped() -> None:
    assert map_to_legacy_score(-1.0) == 0


# ── End-to-end via SkillsDiscover ───────────────────────────────────

def test_discover_uses_bm25f_by_default(tmp_path: Path) -> None:
    """SkillsDiscover uses BM25F (the only ranker, no flag needed)."""
    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))
    discoverer = SkillsDiscover(catalog)
    result = discoverer.discover("drafts", as_root(root), 10)
    assert result.matches[0].skill == "doc-drafts"


def test_discover_drift_falls_back_to_tree(tmp_path: Path) -> None:
    """Drift path: no catalog built → tree scan + loud warning."""
    root = crafted_tree(tmp_path)
    discoverer = SkillsDiscover(SkillsCatalog())
    result = discoverer.discover("notes", as_root(root), 10)
    assert any(m.skill == "note-taker" for m in result.matches)
    assert result.warning != ""


# ── Agent-level execution ───────────────────────────────────────────

def test_agent_discover_uses_bm25f(tmp_path: Path) -> None:
    """The agent's discover path uses BM25F (no ranker flag needed)."""
    from shared.src.skills_design.taxonomy_skills_request import (
        SkillQuery,
        SkillsOp,
        SkillsRequest,
    )

    from skills_design.src.agent_skills_orchestrator import SkillsAgent
    from skills_design.src.capabilities_skills_lister import SkillsLister
    from skills_design.src.capabilities_skills_reader import SkillsPackReader

    root = crafted_tree(tmp_path)
    catalog = SkillsCatalog()
    catalog.rebuild(as_root(root))

    agent = SkillsAgent(
        SkillsLister(root),
        SkillsPackReader(root),
        catalog=catalog,
        discover=SkillsDiscover(catalog),
    )
    request = SkillsRequest(
        op=SkillsOp.DISCOVER,
        query=SkillQuery("notes"),
        root=as_root(root),
        flags={"limit": "10"},
    )
    result = agent.execute(request)
    # BM25F ranker finds note-taker for "notes"
    assert any(m.skill == "note-taker" for m in result.matches)
