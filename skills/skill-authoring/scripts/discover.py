"""Discovery scoring (design §5.6, §6.1).

Scores the catalog rows against a query and renders the results table.
Reads the catalog (``catalog.load_catalog_skill_rows``) rather than the
live tree — the catalog is the index the design makes the drift gate
responsible for, and a read through it is what keeps ``discover``
answering from the same artifact ``catalog --check`` guards.

The scoring is the original ``librarian.py`` ``cmd_discover`` algorithm
verbatim: per-token name +5 / description +3 / category +2 / path +1,
highest score first, then the top ``limit`` rows.
"""

from __future__ import annotations

from pathlib import Path

import catalog
from mutate import fail
from skill_rules import md_escape

__all__ = ["SCORE_TABLE_HEADER", "discover", "score_entries", "tokenize"]

#: The results table header, verbatim from the original ``librarian.py``.
SCORE_TABLE_HEADER = "| Skill | Category | Description | Path | Score |"

#: The separator row under the header, verbatim.
SCORE_TABLE_SEPARATOR = "|---|---|---|---|---|"

#: The empty-result line, verbatim.
NO_MATCH_LINE = "No matching skills found in CATALOG.md."


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


def discover(
    query: str, skills_root: Path, limit: int = 20
) -> tuple[list[str], list[dict[str, object]]]:
    """Search the catalog; returns ``(lines, results)``.

    ``lines`` is the exact report the original ``librarian.py discover``
    printed (header, separator, one row per result, or the single
    no-match line). ``results`` is the machine-readable form ``--json``
    emits. An empty query fails the way the original failed.
    """
    tokens = tokenize(query)
    if not tokens:
        fail("Query is empty")

    rows = catalog.load_catalog_skill_rows(skills_root)
    scored = score_entries(rows, tokens)[:limit]

    if not scored:
        return [NO_MATCH_LINE], []

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

    return lines, results
