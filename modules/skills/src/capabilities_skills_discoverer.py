"""Skills discovery capability (AES capabilities layer).

Scores the catalog rows against a query. Reads the catalog through the
injected ``ISkillsCatalogProtocol`` (never a sibling capability import),
so a read answers from the same artifact ``catalog --check`` guards.

Drift contract: if the catalog fails the drift check (``CatalogDrift`` —
missing, stale, or corrupt), discovery fails **loudly** (a warning the
surface prints to stderr, a ``warning`` field in the ``--json`` result)
and falls back to a read-only tree scan so the answer is real, current
data — never a stale or phantom row. Exit stays 0: a successful search
is a successful search; drift is ``catalog --check``'s exit 3.

The scoring is the original algorithm verbatim: per-token name +5 /
description +3 / category +2 / path +1, highest score first, then the
top ``limit`` rows.
"""

from __future__ import annotations

from pathlib import Path

from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscovererProtocol,
)
from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    CatalogRow,
    DiscoveryMatch,
    DiscoveryResult,
)
from modules.shared.src.skills.taxonomy_skills_error import (
    CatalogDrift,
    SkillsUsageError,
)
from modules.shared.src.skills.taxonomy_skills_vo import SkillsRoot
from modules.shared.src.utility_skills_tree import skill_entries

__all__ = [
    "DRIFT_WARNING",
    "NO_MATCH_LINE",
    "SCORE_TABLE_HEADER",
    "SCORE_TABLE_SEPARATOR",
    "SkillsDiscoverer",
    "score_entries",
    "tokenize",
]

#: The results table header, verbatim from the original ``librarian.py``.
SCORE_TABLE_HEADER = "| Skill | Category | Description | Path | Score |"

#: The separator row under the header, verbatim.
SCORE_TABLE_SEPARATOR = "|---|---|---|---|---|"

#: The empty-result line, verbatim.
NO_MATCH_LINE = "No matching skills found in CATALOG.md."

#: The loud drift warning: the catalog failed its drift gate, so the
#: answer comes from a live tree scan. Named repair: ``aa skills catalog``.
DRIFT_WARNING = (
    "WARNING: catalog drift detected — answering from a live tree scan. "
    "Run `aa skills catalog --check` to repair CATALOG.md."
)


def tokenize(query: str) -> list[str]:
    """Split a query into lowercase tokens."""
    return [token.lower() for token in query.split() if token.strip()]


def score_entries(
    rows: list[CatalogRow], tokens: list[str]
) -> list[tuple[int, CatalogRow]]:
    """Score every row; returns ``(score, row)`` pairs sorted high-first.

    A row scores at all only when at least one token matched, matching the
    original behavior (score 0 rows are never listed).
    """
    scored: list[tuple[int, CatalogRow]] = []

    for row in rows:
        name = row.skill.lower()
        category = row.category.lower()
        description = row.description.lower()
        path = row.path.lower()

        score = 0

        for token in tokens:
            if token in name:
                score += 5
            if token in description:
                score += 3
            if token in category:
                score += 2
            if token in path:
                score += 1

        if score > 0:
            scored.append((score, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored


def tree_scan_rows(skills_root: Path) -> list[CatalogRow]:
    """The read-only tree scan the drift fallback answers from."""
    return [
        CatalogRow(
            skill=entry.skill,
            category=entry.category,
            description=entry.description,
            path=entry.path,
        )
        for entry in skill_entries(skills_root)
    ]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsDiscoverer(ISkillsDiscovererProtocol):
    """Scores catalog rows; falls back to a live tree scan on drift."""

    def __init__(self, catalog: ISkillsCatalogProtocol) -> None:
        self._catalog = catalog

    # ─── Block 2: Protocol Method Implementation ──────────────
    def discover(self, query: str, root: SkillsRoot, limit: int) -> DiscoveryResult:
        """Return the top ``limit`` matches for ``query``."""
        tokens = tokenize(query)
        if not tokens:
            raise SkillsUsageError("Query is empty")

        rows, warning, warning_detail = self._rows_or_fallback(Path(root))
        scored = score_entries(rows, tokens)[:limit]

        matches = tuple(
            DiscoveryMatch(
                skill=row.skill,
                category=row.category,
                description=row.description,
                path=row.path,
                score=score,
            )
            for score, row in scored
        )

        return DiscoveryResult(
            matches=matches,
            warning=warning,
            warning_detail=warning_detail,
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def _rows_or_fallback(
        self, skills_root: Path
    ) -> tuple[list[CatalogRow], str, str]:
        """Load catalog rows; on drift, warn loudly and fall back to the tree."""
        try:
            return list(self._catalog.load_rows(SkillsRoot(skills_root))), "", ""
        except CatalogDrift as drift:
            return tree_scan_rows(skills_root), DRIFT_WARNING, str(drift)
