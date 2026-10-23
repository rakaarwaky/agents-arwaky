"""Discovery scoring and the drift fallback (design §5.6, §6.1).

Scores the catalog rows against a query and renders the results table.
Reads the catalog (``catalog.load_catalog_skill_rows``) rather than the
live tree — the catalog is the index the design makes the drift gate
responsible for, and a read through it is what keeps ``discover``
answering from the same artifact ``catalog --check`` guards.

§5.6 discovery contract: if the catalog fails the drift check
(``catalog.CatalogDrift`` — missing, stale, or corrupt), ``discover``
must fail **loudly** (a stderr warning naming ``catalog --check`` as
the repair command, a ``warning`` field in the ``--json`` result) and
fall back to a read-only tree scan so the answer is real, current
data — never a stale or phantom row. The happy path (in-sync catalog)
keeps the original ``librarian.py`` behavior byte-for-byte.

The scoring is the original ``librarian.py`` ``cmd_discover`` algorithm
verbatim: per-token name +5 / description +3 / category +2 / path +1,
highest score first, then the top ``limit`` rows.
"""

from __future__ import annotations

import sys
from pathlib import Path

import catalog
import model
from mutate import fail
from skill_rules import md_escape

__all__ = [
    "DRIFT_WARNING",
    "SCORE_TABLE_HEADER",
    "discover",
    "score_entries",
    "tokenize",
    "tree_scan_rows",
]

#: The results table header, verbatim from the original ``librarian.py``.
SCORE_TABLE_HEADER = "| Skill | Category | Description | Path | Score |"

#: The separator row under the header, verbatim.
SCORE_TABLE_SEPARATOR = "|---|---|---|---|---|"

#: The empty-result line, verbatim.
NO_MATCH_LINE = "No matching skills found in CATALOG.md."

#: The §5.6 loud warning: the catalog failed its drift gate, so the
#: answer comes from a live tree scan. Named repair: ``catalog --check``.
DRIFT_WARNING = (
    "WARNING: catalog drift detected — answering from a live tree scan. "
    "Run `catalog --check` to repair CATALOG.md."
)


def tokenize(query: str) -> list[str]:
    """Split a query into lowercase tokens."""
    return [token.lower() for token in query.split() if token.strip()]


def score_entries(entries: list[dict[str, str]], tokens: list[str]) -> list[tuple[int, dict[str, str]]]:
    """Score every row; returns ``(score, row)`` pairs sorted high-score-first.

    A row scores at all only when at least one token matched, matching the
    original behavior (score 0 rows are never listed).
    """
    scored: list[tuple[int, dict[str, str]]] = []

    for entry in entries:
        name = entry["skill"].lower()
        category = entry["category"].lower()
        description = entry["description"].lower()
        path = entry["path"].lower()

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
            scored.append((score, entry))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored


def tree_scan_rows(skills_root: Path) -> list[dict[str, str]]:
    """The read-only tree scan §5.6 falls back to when the catalog drifts.

    Live ``model.skill_entries`` data in the exact row shape the
    catalog reader returns, so the scoring path is unchanged — only
    the data source is. This is deliberately the *current* tree: a
    stale or phantom catalog row must never stand in for real data.
    """
    return [
        {
            "skill": entry.skill,
            "category": entry.category,
            "description": entry.description,
            "path": entry.path,
        }
        for entry in model.skill_entries(skills_root)
    ]


def _catalog_rows_or_fallback(skills_root: Path) -> tuple[list[dict[str, str]], str | None]:
    """Load the catalog rows; on drift, warn loudly and fall back to the tree.

    §5.6: the fallback is never silent — the warning names
    ``catalog --check`` as the repair. The warning text is returned
    (``None`` on the happy path) so ``--json`` can carry it as a
    field without polluting the table stdout.
    """
    try:
        return catalog.load_catalog_skill_rows(skills_root), None
    except catalog.CatalogDrift as drift:
        print(DRIFT_WARNING, file=sys.stderr)
        print(f"  reason: {drift}", file=sys.stderr)
        return tree_scan_rows(skills_root), DRIFT_WARNING


def discover(
    query: str, skills_root: Path, limit: int = 20
) -> tuple[list[str], list[dict[str, object]], str | None]:
    """Search the catalog; returns ``(lines, results, warning)``.

    ``lines`` is the exact report the original ``librarian.py discover``
    printed (header, separator, one row per result, or the single
    no-match line). ``results`` is the machine-readable form ``--json``
    emits. ``warning`` is the §5.6 drift-fallback warning text when the
    catalog failed its drift check and the answer came from the live
    tree scan instead (``None`` on the happy path). An empty query
    fails the way the original failed.
    """
    tokens = tokenize(query)
    if not tokens:
        fail("Query is empty")

    rows, warning = _catalog_rows_or_fallback(skills_root)
    scored = score_entries(rows, tokens)[:limit]

    if not scored:
        return [NO_MATCH_LINE], [], warning

    lines = [SCORE_TABLE_HEADER, SCORE_TABLE_SEPARATOR]
    results: list[dict[str, object]] = []

    for score, row in scored:
        lines.append(
            f"| {md_escape(row['skill'])} "
            f"| {md_escape(row['category'])} "
            f"| {md_escape(row['description'])} "
            f"| {md_escape(row['path'])} "
            f"| {score} |"
        )
        results.append(
            {
                "skill": row["skill"],
                "category": row["category"],
                "description": row["description"],
                "path": row["path"],
                "score": score,
            }
        )

    return lines, results, warning
