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

The scoring is the original algorithm verbatim: per-token name +5 /
description +3 / category +2 / path +1, highest score first, then the
top ``limit`` rows.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from shared.src.common.utility_skills_tree import skill_entries
from shared.src.skills_design.contract_skills_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
)
from shared.src.skills_design.taxonomy_skills_authoring_vo import (
    DiscoveryMatch,
    DiscoveryResult,
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
    "score_entries",
    "tokenize",
]


@dataclass(frozen=True)
class _Row:
    """One catalog row the discover capability scores."""

    skill: str
    category: str
    description: str
    path: str


def tokenize(query: str) -> list[str]:
    """Split a query into lowercase tokens."""
    return [token.lower() for token in query.split() if token.strip()]


def score_entries(
    rows: list[_Row], tokens: list[str]
) -> list[tuple[int, _Row]]:
    """Score every row; returns ``(score, row)`` pairs sorted high-first.

    A row scores at all only when at least one token matched, matching the
    original behavior (score 0 rows are never listed).
    """
    scored: list[tuple[int, _Row]] = []

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


def tree_scan_rows(skills_root: Path) -> list[_Row]:
    """The read-only tree scan the drift fallback answers from."""
    return [
        _Row(
            skill=entry.skill,
            category=entry.category,
            description=entry.description,
            path=entry.path,
        )
        for entry in skill_entries(skills_root)
    ]


# ─── Block 1: Class Definition & Constructor ──────────────
class SkillsDiscover(ISkillsDiscoverProtocol):
    """Scores catalog rows; falls back to a live tree scan on drift."""

    def __init__(self, catalog: ISkillsCatalogProtocol) -> None:
        self._catalog = catalog

    # ─── Block 2: Protocol Method Implementation ──────────────
    def discover(self, query: SkillQuery, root: SkillsRoot, limit: int) -> DiscoveryResult:
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
                )
            )

        if not rows:
            return tree_scan_rows(skills_root), DRIFT_WARNING, f"Catalog empty: {path}"

        return rows, "", ""
