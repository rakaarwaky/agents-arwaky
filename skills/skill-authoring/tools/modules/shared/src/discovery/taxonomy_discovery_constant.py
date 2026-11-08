"""Discovery BM25F ranking constants (AES taxonomy layer).

The tunable parameters of the offline BM25F field-weighted ranker the
``SkillsDiscover`` capability scores catalog rows with: the per-field
weights, the fuzzy-match thresholds, the English + Indonesian stop-word
sets, and the logical-field → row-attribute mapping.

Consumed by ``shared.src.discovery.taxonomy_discovery_vo`` (the ranker
VO) — the capability itself never restates these values.
"""

from __future__ import annotations

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

#: English stop words dropped before indexing.
STOP_WORDS: frozenset[str] = frozenset(
    ["a", "an", "the", "this", "that", "these", "those", "to", "of", "in", "on", "for", "from", "with", "and", "or", "is", "are", "be", "it", "its", "as", "at", "by", "my", "me", "i", "you", "your", "please", "supplied", "attached", "existing", "not", "do", "does", "no", "into", "using", "use", "their", "them", "then", "than", "just", "only", "can", "should", "would", "could", "what", "which", "how"]
)

#: Indonesian stop words dropped before indexing.
_INDONESIAN_STOP_WORDS: frozenset[str] = frozenset(
    ["saya", "kau", "kamu", "dia", "kami", "kita", "anda", "mereka", "itu", "ini", "dan", "atau", "namun", "tetapi", "yang", "dengan", "dari", "pada", "untuk", "adalah", "akan", "bisa", "tidak", "ya", "apa", "bagaimana", "mengapa", "kapan", "mana", "sudah", "belum", "mau", "juga", "pun", "saja", "hanya", "hendak", "ingin", "telah"]
)

#: Combined stop-words (English + Indonesian).
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


__all__ = [
    "BM25F_FIELD_WEIGHTS",
    "MIN_TOKEN_LEN",
    "SIMILARITY_THRESHOLD",
    "STOP_WORDS",
    "_ALL_STOP_WORDS",
    "_FIELD_ATTR",
    "_INDONESIAN_STOP_WORDS",
    "_RANKER_FIELDS",
]
