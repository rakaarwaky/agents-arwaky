"""BM25F field-weighted ranking for skill discovery (AES capabilities layer).

Re-ranks catalog rows with a fuzzy token-similarity scorer. Each field
carries a weight mirroring the legacy discover weights (name 5,
description 3, category 2, path 1). For each query token, we find every
skill token that is "close enough" (substring in either direction, or
Jaccard character similarity ≥ 0.75) and score the match.

No network, no third-party dependencies, no paid model. Offline by design.

Row objects passed to :func:`rank` must have the four attributes
``skill``, ``category``, ``description``, and ``path`` (the shape of
the discover ``_Row``).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from dataclasses import field as dataclass_field

__all__ = [
    "BM25F_FIELD_WEIGHTS",
    "build_index",
    "map_to_legacy_score",
    "rank_bm25f",
    "tokenize_full",
]

# ── Constants ──────────────────────────────────────────────────────────

#: Field weights: name +5, when_to_use +4, description +3, category +2, path +1.
BM25F_FIELD_WEIGHTS: dict[str, float] = {
    "name": 5.0,
    "when_to_use": 4.0,
    "description": 3.0,
    "category": 2.0,
    "path": 1.0,
}

#: Minimum character-set Jaccard similarity for a fuzzy match.
SIMILARITY_THRESHOLD: float = 0.75

#: Minimum token length for a fuzzy match to count.
MIN_TOKEN_LEN: int = 3

#: Score scale factor: float score * scale → int for legacy projection.
BM25F_SCORE_SCALE: int = 100

#: English stop words dropped before indexing.
STOP_WORDS: frozenset[str] = frozenset(
    ["a", "an", "the", "this", "that", "these", "those", "to", "of", "in", "on", "for", "from", "with", "and", "or", "is", "are", "be", "it", "its", "as", "at", "by", "my", "me", "i", "you", "your", "please", "supplied", "attached", "existing", "not", "do", "does", "no", "into", "using", "use", "their", "them", "then", "than", "just", "only", "can", "should", "would", "could", "what", "which", "how"]
)

#: Indonesian stop words dropped before indexing.
_INDONESIAN_STOP_WORDS: frozenset[str] = frozenset(
    ["saya", "kau", "kamu", "dia", "kami", "kita", "anda", "mereka", "itu", "ini", "dan", "atau", "namun", "tetapi", "yang", "dengan", "dari", "pada", "untuk", "adalah", "akan", "bisa", "tidak", "ya", "apa", "bagaimana", "mengapa", "kapan", "mana", "sudah", "belum", "mau", "juga", "pun", "saja", "hanya", "hendak", "ingin", "telah"]
)

# Combined stop-words (English + Indonesian).
_ALL_STOP_WORDS: frozenset[str] = STOP_WORDS | _INDONESIAN_STOP_WORDS

#: Logical field names. The row attribute that backs each field:
#: "name" maps to the row's ``skill`` attribute (legacy frontmatter name).
_FIELD_ATTR: dict[str, str] = {
    "name": "skill",
    "when_to_use": "when_to_use",
    "description": "description",
    "category": "category",
    "path": "path",
}
_RANKER_FIELDS: tuple[str, ...] = ("name", "when_to_use", "description", "category", "path")


def tokenize_full(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, drop stop words and short tokens."""
    return [
        tok
        for tok in re.findall(r"[a-z0-9]+", text.lower())
        if tok not in _ALL_STOP_WORDS and len(tok) >= MIN_TOKEN_LEN
    ]


# ── Similarity helpers ─────────────────────────────────────────────────


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


def _tokens_similar(query_tok: str, skill_tok: str) -> bool:
    """True when two tokens are similar enough to count as a match.

    A match fires when either:
    * one token is a substring of the other (min length 3)
    * both tokens ≥ 4 chars and character-set Jaccard similarity
      ≥ SIMILARITY_THRESHOLD
    """
    if len(query_tok) < MIN_TOKEN_LEN or len(skill_tok) < MIN_TOKEN_LEN:
        return False
    # Substring (either direction)
    if query_tok in skill_tok or skill_tok in query_tok:
        return True
    # Jaccard char-set similarity (both tokens must be ≥ 4 chars to
    # avoid noise from very short tokens).
    if len(query_tok) < 4 or len(skill_tok) < 4:
        return False
    return _jaccard(query_tok, skill_tok) >= SIMILARITY_THRESHOLD


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


# ── Index ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _BM25FRow:
    """Internal indexed row: original attributes + precomputed per-field tokens."""

    skill: str
    category: str
    description: str
    path: str
    when_to_use: str = ""
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


# ── Fuzzy BM25F ranking ───────────────────────────────────────────────


def rank_bm25f(rows, tokens: list[str]) -> list[tuple[float, object]]:
    """Return ``(score, row)`` pairs sorted high-first.

    For each query token, we scan every skill token in every field and
    accumulate a similarity-weighted BM25F-style score. Exact matches
    score 1.0, substring matches 0.9, Jaccard ≥ 0.75 scores 0.7–1.0.

    The score formula per field:
        field_score = Σ over matched (query_tok, skill_tok) pairs of
                      strength(q, s) * IDF(s) * tf(s) / tf_norm

    This is a fuzzy relaxation of BM25F that bridges morphological and
    cross-language gaps (e.g. "mengimplementasikan" ↔ "implement").
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
    # Also tokenize and deduplicate
    extra_stems = tokenize_full(" ".join(query_tokens))
    for t in extra_stems:
        if t not in seen_q:
            query_tokens.append(t)
            seen_q.add(t)

    if not query_tokens:
        return []

    scored: list[tuple[float, object]] = []
    for row in index.rows:
        score = 0.0
        for logical in _RANKER_FIELDS:
            weight = BM25F_FIELD_WEIGHTS[logical]
            skill_toks = row.fields[logical]
            if not skill_toks:
                continue
            dl = row.field_len[logical]
            if dl == 0:
                continue

            field_score = 0.0
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
                    # Use the IDF of the best-matching skill token (not the
                    # query token, which is almost always absent from the
                    # corpus and would default to max-idf for every skill).
                    idf = _idf(index, logical, best_skill_tok)
                    if idf == 0.0:
                        idf = 1.0
                    field_score += best_strength * idf
            score += weight * field_score

        if score > 0:
            scored.append((score, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored


def map_to_legacy_score(score: float) -> int:
    """Map a float BM25F score to the legacy int score projection."""
    return max(0, round(score * BM25F_SCORE_SCALE))
