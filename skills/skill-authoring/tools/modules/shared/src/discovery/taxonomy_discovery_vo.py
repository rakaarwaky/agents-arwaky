"""Discovery ranker value objects (AES taxonomy layer).

The offline BM25F field-weighted ranker (``SkillsBm25fRanker``) plus the
stateless free functions it rides on: ``tokenize`` (query → lowercase
tokens), ``rank_bm25f`` / ``build_index`` / ``_idf`` /
``tokenize_full`` / the match-strength helpers.

The ranking parameters they consume live in
``taxonomy_discovery_constant``; the row/hit shapes they score come from
the common domain's taxonomy VO module.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
The drift-fallback tree scan (``tree_scan_rows``) moved to the capability
layer (``capabilities_discovery_finder``) to keep the taxonomy layer
free of filesystem I/O and of the taxonomy→utility edge that created
the AES205 cycle.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from shared.src.common.taxonomy_common_vo import BM25FHit
from shared.src.discovery.taxonomy_discovery_constant import (
    _ALL_STOP_WORDS,
    _FIELD_ATTR,
    _RANKER_FIELDS,
    BM25F_FIELD_WEIGHTS,
    MIN_TOKEN_LEN,
    SIMILARITY_THRESHOLD,
)

__all__ = [
    "SkillsBm25fRanker",
    "build_index",
    "rank_bm25f",
    "tokenize",
    "tokenize_full",
]


@dataclass(frozen=True)
class _BM25FIndex:
    rows: tuple[_BM25FRow, ...]
    n_docs: int
    avgdl: dict[str, float]
    df: dict[str, dict[str, int]]  # logical field → token → doc count


@dataclass(frozen=True)
class _BM25FRow:
    """Internal indexed row: original attributes + precomputed per-field tokens."""

    skill: str
    category: str
    description: str
    path: str
    when_to_use: str = ""
    fields: dict[str, list[str]] = field(default_factory=dict)
    field_len: dict[str, int] = field(default_factory=dict)


def build_index(rows) -> _BM25FIndex:
    """Precompute everything ``rank_bm25f`` needs for *rows*."""
    bm25_rows: list[_BM25FRow] = []
    df: dict[str, dict[str, int]] = {f: {} for f in _RANKER_FIELDS}

    for row in rows:
        fields: dict[str, list[str]] = {}
        field_len: dict[str, int] = {}
        for logical in _RANKER_FIELDS:
            attr = _FIELD_ATTR[logical]
            text = getattr(row, attr, "") or ""
            tokens = tokenize_full(text)
            fields[logical] = tokens
            field_len[logical] = len(tokens)
            seen: set[str] = set()
            for tok in tokens:
                if tok in seen:
                    continue
                seen.add(tok)
                df[logical][tok] = df[logical].get(tok, 0) + 1
        bm25_rows.append(
            _BM25FRow(
                skill=getattr(row, "skill", ""),
                category=getattr(row, "category", ""),
                description=getattr(row, "description", ""),
                path=getattr(row, "path", ""),
                when_to_use=getattr(row, "when_to_use", ""),
                fields=fields,
                field_len=field_len,
            )
        )

    n_docs = len(bm25_rows)
    avgdl = {
        f: (sum(r.field_len[f] for r in bm25_rows) / n_docs) if n_docs else 0.0
        for f in _RANKER_FIELDS
    }
    return _BM25FIndex(
        rows=tuple(bm25_rows),
        n_docs=n_docs,
        avgdl=avgdl,
        df=df,
    )


def _idf(index: _BM25FIndex, field: str, token: str) -> float:
    n = index.n_docs
    n_ti = index.df[field].get(token, 0)
    if n_ti == 0:
        return 0.0
    # Robertson–Spac–Walker (log base e, +1 shift): always > 0.
    return math.log((n - n_ti + 0.5) / (n_ti + 0.5)) + 1.0


def rank_bm25f(rows, tokens: list[str]) -> list[BM25FHit]:
    """Return ``BM25FHit`` results sorted high-first.

    Each hit carries the float ``score``, the original row object, and
    ``matched_fields`` — the logical field names that contributed.
    """
    if not rows or not tokens:
        return []
    index = build_index(rows)
    query_tokens: list[str] = []
    seen_q: set[str] = set()
    for t in tokens:
        t = t.lower()
        if t not in _ALL_STOP_WORDS and t not in seen_q:
            query_tokens.append(t)
            seen_q.add(t)
    extra_stems = tokenize_full(" ".join(query_tokens))
    for t in extra_stems:
        if t not in seen_q:
            query_tokens.append(t)
            seen_q.add(t)

    if not query_tokens:
        return []

    hits: list[BM25FHit] = []
    for row in index.rows:
        score = 0.0
        matched: list[str] = []
        for logical in _RANKER_FIELDS:
            weight = BM25F_FIELD_WEIGHTS[logical]
            skill_toks = row.fields[logical]
            if not skill_toks:
                continue
            dl = row.field_len[logical]
            if dl == 0:
                continue

            field_score = 0.0
            field_matched = False
            for q_tok in query_tokens:
                if len(q_tok) < MIN_TOKEN_LEN:
                    continue
                best_strength = 0.0
                best_skill_tok = ""
                for s_tok in skill_toks:
                    strength = _match_strength(q_tok, s_tok)
                    if strength > best_strength:
                        best_strength = strength
                        best_skill_tok = s_tok
                if best_strength > 0 and best_skill_tok:
                    idf = _idf(index, logical, best_skill_tok)
                    if idf == 0.0:
                        idf = 1.0
                    field_score += best_strength * idf
                    field_matched = True
            if field_matched:
                matched.append(logical)
            score += weight * field_score

        if score > 0:
            hits.append(BM25FHit(score=score, row=row, matched_fields=tuple(sorted(matched))))

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits


class SkillsBm25fRanker:
    """Offline BM25F field-weighted ranker over catalog rows.

    ``rank`` returns ``BM25FHit`` results sorted high-first. The stateless
    algorithm also lives as module-level free functions (``rank_bm25f``)
    for direct callers.
    """

    def rank(self, rows: object, tokens: list[str]) -> list[BM25FHit]:
        """Score *rows* against *tokens*; empty input yields an empty list."""
        return rank_bm25f(rows, tokens)

    def __repr__(self) -> str:
        return "SkillsBm25fRanker()"


def tokenize(query: str) -> list[str]:
    """Split a query into lowercase tokens (stop-word filtering happens in BM25F)."""
    return [token.lower() for token in query.split() if token.strip()]


def tokenize_full(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, drop stop words and short tokens."""
    return [
        tok
        for tok in re.findall(r"[a-z0-9]+", text.lower())
        if tok not in _ALL_STOP_WORDS and len(tok) >= MIN_TOKEN_LEN
    ]


def _char_set(token: str) -> set[str]:
    return set(token)


def _jaccard(a: str, b: str) -> float:
    """Character-set Jaccard similarity between two strings."""
    sa, sb = _char_set(a), _char_set(b)
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def _match_strength(query_tok: str, skill_tok: str) -> float:
    """Return a strength in [0, 1] for a fuzzy match; 0 means no match.

    Exact match → 1.0. Substring → 0.9. Jaccard ≥ threshold → 0.7 +
    0.3 * jaccard (so 0.75 → 0.925, 1.0 → 1.0). Jaccard requires both
    tokens ≥ 4 chars to avoid noise from very short tokens.
    """
    if query_tok == skill_tok:
        return 1.0
    if len(query_tok) >= MIN_TOKEN_LEN and (query_tok in skill_tok or skill_tok in query_tok):
        return 0.9
    if len(query_tok) >= 4 and len(skill_tok) >= 4:
        jac = _jaccard(query_tok, skill_tok)
        if jac >= SIMILARITY_THRESHOLD:
            return 0.7 + 0.3 * jac
    return 0.0
