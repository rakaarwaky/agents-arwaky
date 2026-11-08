"""Unit tests: BM25F ranker ranking and scoring math for discovery."""
from __future__ import annotations

import sys
from pathlib import Path

_MOD_ROOT = Path(__file__).resolve().parent.parent.parent
for _ns in (_MOD_ROOT,):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))

from discovery.capabilities_discovery_finder import (
    BM25F_FIELD_WEIGHTS,
    SkillsBm25fRanker,
    build_index,
    rank_bm25f,
    tokenize,
)
from shared.src.design.taxonomy_skills_vo import _Row


def _row(skill: str, description: str, category: str = "automation") -> _Row:
    return _Row(
        skill=skill,
        category=category,
        description=description,
        path=f"{category}/{skill}",
        when_to_use="",
    )


def test_tokenize_lowercases_and_drops_short_words():
    """UT-DISCOVERY-001: tokenize lowercases and drops stop/short tokens."""
    tokens = tokenize("How do I list skills?")
    assert tokens == ["list", "skill"]


def test_ranker_ranks_relevant_skill_first():
    """UT-DISCOVERY-002: BM25F puts the most relevant skill on top."""
    ranker = SkillsBm25fRanker()
    rows = [
        _row("fetch-mcp", "Fetch web content via the MCP tool."),
        _row("backup", "Backup tar archives."),
    ]
    hits = ranker.rank(rows, tokenize("list fetch content"))
    assert len(hits) > 0
    assert hits[0].row.skill == "fetch-mcp"


def test_build_index_computes_field_stats():
    """UT-DISCOVERY-003: build_index precomputes field-level stats."""
    rows = [_row("a", "alpha beta"), _row("b", "alpha gamma")]
    index = build_index(rows)
    assert index.n_docs == 2
    assert index.avgdl["name"] >= 0.0


def test_field_weights_are_declared():
    """UT-DISCOVERY-004: name weighs heaviest in BM25F."""
    assert BM25F_FIELD_WEIGHTS["name"] == 5.0
    assert BM25F_FIELD_WEIGHTS["description"] == 3.0
