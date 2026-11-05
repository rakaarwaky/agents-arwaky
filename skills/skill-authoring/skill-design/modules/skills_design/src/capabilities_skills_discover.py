"""Skills discover capability (AES capabilities layer).

Scores the catalog rows against a query. Reads the tracked
``catalog.json`` through the injected ``ISkillsCatalogProtocol``
(never a sibling capability import), so a read answers from the same
artifact ``catalog --check`` guards.

Drift contract: if the catalog is missing, corrupt, or empty, discovery
fails **loudly** (a warning the surface prints to stderr, a ``warning``
field in the ``--json`` result) and falls back to a read-only tree scan
so the answer is real, current data — never a stale or phantom row.
Exit stays 0: a successful search is a successful search; drift is
``catalog --check``'s exit 3.

The only ranker is **bm25f** — offline BM25F field-weighted ranking
(see :mod:`capabilities_skills_bm25f`), with field weights (5/3/2/1)
and stop-word filtering. No network, no third-party deps, no paid or
closed model.

Float BM25F scores are mapped to ints via ``map_to_legacy_score`` so
the table projection and the ``score`` int on ``DiscoveryMatch`` stay
stable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from shared.src.common.utility_skills_tree import skill_entries
from shared.src.skills_design.contract_skills_bm25f_protocol import (
    IBM25FRankerProtocol,
)
from shared.src.skills_design.contract_skills_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
)
from shared.src.skills_design.taxonomy_skills_authoring_vo import (
    DiscoveryMatch,
    DiscoveryResult,
    map_to_legacy_score,
)
from shared.src.skills_design.taxonomy_skills_constant import (
    CATALOG_FILENAME,
    DRIFT_WARNING,
)
from shared.src.skills_design.taxonomy_skills_error import (
    SkillsUsageError,
)
from shared.src.skills_design.taxonomy_skills_request import (
    SkillQuery,
    SkillsRoot,
)

__all__ = [
    "SkillsDiscover",
    "tokenize",
]


@dataclass(frozen=True)
class _Row:
    """One catalog row the discover capability scores."""

    skill: str
    category: str
    description: str
    path: str
    when_to_use: str = ""


def tokenize(query: str) -> list[str]:
    """Split a query into lowercase tokens (stop-word filtering happens in BM25F)."""
    return [token.lower() for token in query.split() if token.strip()]


def tree_scan_rows(skills_root: Path) -> list[_Row]:
    """The read-only tree scan the drift fallback answers from."""
    return [
        _Row(
            skill=entry.skill,
            category=entry.category,
            description=entry.description,
            path=entry.path,
            when_to_use=getattr(entry, "when_to_use", ""),
        )
        for entry in skill_entries(skills_root)
    ]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsDiscover(ISkillsDiscoverProtocol):
    """Scores catalog rows with BM25F; falls back to a live tree scan on drift."""

    def __init__(
        self,
        catalog: ISkillsCatalogProtocol,
        ranker: IBM25FRankerProtocol | None = None,
    ) -> None:
        self._catalog = catalog
        self._ranker = ranker

    # ─── Block 2: Protocol Method Implementation ──────────────
    def discover(self, query: SkillQuery, root: SkillsRoot, limit: int) -> DiscoveryResult:
        """Return the top ``limit`` matches for ``query`` (BM25F)."""
        tokens = tokenize(query)
        if not tokens:
            raise SkillsUsageError("Query is empty")

        rows, warning, warning_detail = self._rows_or_fallback(Path(root))
        ranker = self._ranker if self._ranker is not None else _default_ranker()
        scored = ranker.rank(rows, tokens)[:limit]

        matches = tuple(
            DiscoveryMatch(
                skill=hit.row.skill,
                category=hit.row.category,
                description=hit.row.description,
                path=hit.row.path,
                score=map_to_legacy_score(hit.score),
                matched_fields=hit.matched_fields,
            )
            for hit in scored
        )

        return DiscoveryResult(
            matches=matches,
            warning=warning,
            warning_detail=warning_detail,
        )

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def _rows_or_fallback(
        self, skills_root: Path
    ) -> tuple[list[_Row], str, str]:
        """Load catalog rows from catalog.json; on missing/stale, fall back to tree scan."""
        path = skills_root / CATALOG_FILENAME
        text = self._catalog.read(SkillsRoot(skills_root))
        if not text:
            return tree_scan_rows(skills_root), DRIFT_WARNING, f"Catalog missing: {path}"

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return tree_scan_rows(skills_root), DRIFT_WARNING, f"Catalog corrupt: {path}"

        skills = data.get("skills") if isinstance(data, dict) else None
        if not isinstance(skills, list):
            return tree_scan_rows(skills_root), DRIFT_WARNING, f"Catalog corrupt: {path}"

        rows: list[_Row] = []
        for item in skills:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            category = str(item.get("category", ""))
            rows.append(
                _Row(
                    skill=name,
                    category=category,
                    description=str(item.get("description", "")),
                    path=f"{category}/{name}",
                    when_to_use=str(item.get("when_to_use", "")),
                )
            )

        if not rows:
            return tree_scan_rows(skills_root), DRIFT_WARNING, f"Catalog empty: {path}"

        return rows, "", ""


# ── Module-level helpers (stateless, no I/O, no cross-layer deps) ─────


def _default_ranker() -> IBM25FRankerProtocol:
    """Lazily instantiate the default BM25F ranker (avoids circular import)."""
    from skills_design.src.capabilities_skills_bm25f import SkillsBm25fRanker

    return SkillsBm25fRanker()


def _map_to_legacy_score(score: float) -> int:
    """Map a float BM25F score to the legacy int projection."""
    from skills_design.src.capabilities_skills_bm25f import map_to_legacy_score

    return map_to_legacy_score(score)
