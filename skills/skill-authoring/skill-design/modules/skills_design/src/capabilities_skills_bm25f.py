"""BM25F field-weighted ranking for skill discovery (AES capabilities layer).

Re-ranks catalog rows with BM25F (Best Match 25, field-weighted). Each
field carries a weight mirroring the legacy discover weights (name 5,
description 3, category 2, path 1). Scores are float; the caller maps
them back to the legacy int projection via :func:`map_to_legacy_score`.

No network, no third-party dependencies, no paid model. Offline by
design.

Row objects passed to :func:`rank_bm25f` must have the four attributes
``skill``, ``category``, ``description``, and ``path`` (the shape of the
discover ``_Row``). The field-name → attribute mapping is:
``"name"`` → ``skill``, ``"category"`` → ``category``,
``"description"`` → ``description``, ``"path"`` → ``path``.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field as dataclass_field

__all__ = [
    "BM25F_FIELD_WEIGHTS",
    "build_index",
    "map_to_legacy_score",
    "rank_bm25f",
    "tokenize_full",
]

# ── Constants ──────────────────────────────────────────────────────────

BM25F_K1: float = 1.5
BM25F_B: float = 0.75
BM25F_SCORE_SCALE: int = 100  # float score * scale → int for legacy projection

#: Field weights mirroring legacy discover (name +5 / description +3 /
#: category +2 / path +1).
BM25F_FIELD_WEIGHTS: dict[str, float] = {
    "name": 5.0,
    "description": 3.0,
    "category": 2.0,
    "path": 1.0,
}

#: English stop words dropped before indexing.
STOP_WORDS: frozenset[str] = frozenset(
    "a an the this that these those to of in on for from with and or is are be it its "
    "as at by my me i you your please supplied attached existing not do does no into "
    "using use their them then than just only can should would could what which how"
    .split()
)

#: Logical field names. The row attribute that backs each field:
#: "name" maps to the row's ``skill`` attribute (legacy frontmatter name).
_FIELD_ATTR: dict[str, str] = {
    "name": "skill",
    "description": "description",
    "category": "category",
    "path": "path",
}
_RANKER_FIELDS: tuple[str, ...] = ("name", "description", "category", "path")


def tokenize_full(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics (incl. hyphens), drop stop words."""
    return [tok for tok in re.findall(r"[a-z0-9]+", text.lower()) if tok not in STOP_WORDS]


@dataclass(frozen=True)
class _BM25FRow:
    """Internal indexed row: original attributes + precomputed per-field tokens."""

    skill: str
    category: str
    description: str
    path: str
    # Per-field token lists, keyed by logical field name.
    fields: dict[str, list[str]] = dataclass_field(default_factory=dict)
    # Per-field token counts.
    field_len: dict[str, int] = dataclass_field(default_factory=dict)


@dataclass(frozen=True)
class _BM25FIndex:
    rows: tuple[_BM25FRow, ...]
    n_docs: int
    avgdl: dict[str, float]
    df: dict[str, dict[str, int]]  # logical field → token → doc count


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


def rank_bm25f(rows, tokens: list[str]) -> list[tuple[float, object]]:
    """Return ``(score, row)`` pairs sorted high-first.

    ``score`` is a float BM25F value (raw, not scaled). Rows with zero
    score across all fields are excluded, matching the legacy contract
    that score-0 rows are never listed.
    """
    if not rows or not tokens:
        return []
    index = build_index(rows)
    query_tokens = [t for t in tokenize_full(" ".join(tokens)) if t]
    if not query_tokens:
        return []

    scored: list[tuple[float, object]] = []
    for row in index.rows:
        score = 0.0
        for logical in _RANKER_FIELDS:
            weight = BM25F_FIELD_WEIGHTS[logical]
            tokens_field = row.fields[logical]
            if not tokens_field:
                continue
            dl = row.field_len[logical]
            if dl == 0:
                continue
            avgdl = index.avgdl[logical]
            if avgdl:
                denom = BM25F_K1 * (1 - BM25F_B + BM25F_B * (dl / avgdl))
            else:
                denom = BM25F_K1
            field_score = 0.0
            seen: set[str] = set()
            for tok in query_tokens:
                if tok in seen:
                    continue
                seen.add(tok)
                tf = tokens_field.count(tok)
                if tf == 0:
                    continue
                idf = _idf(index, logical, tok)
                if idf == 0.0:
                    continue
                field_score += idf * ((tf * (BM25F_K1 + 1)) / (tf + denom))
            score += weight * field_score
        if score > 0:
            scored.append((score, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored


def map_to_legacy_score(score: float) -> int:
    """Map a float BM25F score to the legacy int score projection."""
    return max(0, round(score * BM25F_SCORE_SCALE))
