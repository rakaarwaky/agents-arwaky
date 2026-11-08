"""Skills discover capability (AES capabilities layer).

Scores catalog rows against a query with the only ranker — BM25F
field-weighted ranking — then falls back to a live tree scan on catalog
drift. Reads ``catalog.json`` through the injected ``ISkillsCatalogProtocol``
(never a sibling capability import), so a read answers from the same
artifact ``catalog --check`` guards.

Drift contract: if the catalog is missing, corrupt, or empty, discovery
fails **loudly** (a warning printed to stderr, a ``warning`` field in the
``--json`` result) and falls back to a read-only tree scan so the answer is
real, current data — never a stale or phantom row. Exit stays 0: a
successful search is a successful search; drift is ``catalog --check``'s
exit 3.

Float BM25F scores are mapped to ints via ``map_to_legacy_score`` so the
table projection and the ``score`` int on ``DiscoveryMatch`` stay stable.
"""

from __future__ import annotations

import json
from pathlib import Path

from shared.src.common.taxonomy_common_constant import (
    CATALOG_FILENAME,
    DRIFT_WARNING,
)
from shared.src.common.taxonomy_common_error import (
    SkillsUsageError,
)
from shared.src.common.taxonomy_common_vo import (
    DiscoveryMatch,
    DiscoveryResult,
    _Row,
    map_to_legacy_score,
)
from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
)
from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryQuery,
    DiscoveryRoot,
)
from shared.src.discovery.taxonomy_discovery_vo import (
    BM25FHit,
    SkillsBm25fRanker,
    tokenize,
)
from shared.src.discovery.utility_discovery_core import skill_entries

__all__ = [
    "SkillsDiscover",
    "tree_scan_rows",
]


def tree_scan_rows(skills_root: Path) -> list[_Row]:
    """The read-only tree scan the drift fallback answers from.

    Moved from ``taxonomy_discovery_vo.py`` to the capability layer:
    the taxonomy layer must stay free of filesystem I/O and of the
    taxonomy→utility edge that created the AES205 cycle.
    """
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


# ─── Block 1: Module Declaration ───
class SkillsDiscover(ISkillsDiscoverProtocol):
    """Scores catalog rows with BM25F; falls back to a live tree scan on drift."""

    def __init__(
        self,
        catalog: ISkillsCatalogProtocol,
        ranker: SkillsBm25fRanker,
    ) -> None:
        self._catalog = catalog
        self._ranker = ranker

    # ─── Block 2: Module Contract ───
    def discover(self, query: DiscoveryQuery, root: DiscoveryRoot, limit: int) -> DiscoveryResult:
        """Return the top ``limit`` matches for ``query`` (BM25F)."""
        tokens = tokenize(query)
        if not tokens:
            raise SkillsUsageError("Query is empty")

        rows, warning, warning_detail = self._rows_or_fallback(Path(root))
        scored = self._ranker.rank(rows, tokens)[:limit]

        matches = tuple(
            DiscoveryMatch(
                skill=hit.row.skill,
                category=hit.row.category,
                description=hit.row.description,
                path=hit.row.path,
                score=map_to_legacy_score(hit.score),
                matched_fields=hit.matched_fields,
                when_to_use=getattr(hit.row, "when_to_use", ""),
            )
            for hit in scored
        )

        return DiscoveryResult(
            matches=matches,
            warning=warning,
            warning_detail=warning_detail,
        )

    def rank(self, rows: object, tokens: list[str]) -> list[BM25FHit]:
        """Score *rows* against *tokens* with the injected BM25F ranker."""
        return self._ranker.rank(rows, tokens)

    # ─── Block 3: Module Helpers ───
    def _rows_or_fallback(
        self, skills_root: Path
    ) -> tuple[list[_Row], str, str]:
        """Load catalog rows from catalog.json; on missing/stale, fall back to tree scan."""
        path = skills_root / CATALOG_FILENAME
        text = self._catalog.read(DiscoveryRoot(skills_root))
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
