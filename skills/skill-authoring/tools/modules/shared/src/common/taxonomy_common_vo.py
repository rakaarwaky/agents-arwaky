"""Shared-kernel value objects for the skills domain (AES common layer).

Pure-data VOs that are consumed by more than one module domain
(discovery, design, storage, maintenance, governance, observability).
A module must import these from here rather than reaching into a
sibling domain's taxonomy module.

Everything here is pure data with no I/O.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, NewType

from shared.src.common.taxonomy_common_constant import BM25F_SCORE_SCALE

# ─── Core read-side primitives ─────────────────────────────────────────

SkillContent = NewType("SkillContent", str)
"""Raw SKILL.md text returned by a read."""

SkillDescription = NewType("SkillDescription", str)
"""One-line description extracted from SKILL.md frontmatter."""

ErrorMessage = NewType("ErrorMessage", str)
"""A formatted error message for skill-domain exceptions."""

SkillsJsonPayload = NewType("SkillsJsonPayload", Mapping[str, object])
"""The pure-data JSON list of global skills (``SkillsLister.list_skills_json``).

One entry per skill (``name``, ``source``, ``path``, ``loaded``); the
source is the repo pack only. A pure-data dict, so it never touches I/O.
"""


@dataclass(frozen=True)
class SkillRecord:
    """One discoverable skill in the pack."""

    name: str
    description: SkillDescription
    path: Path


# ─── Skill reference value objects ─────────────────────────────────────

#: A skill directory name (the folder name under a category).
SkillName = NewType("SkillName", str)

#: A category directory name.
CategoryName = NewType("CategoryName", str)


# ─── Discovery / catalog value objects ─────────────────────────────────


def map_to_legacy_score(score: float) -> int:
    """Map a float BM25F score to the legacy int score projection.

    Pure data helper (no I/O, no imports from utility/capabilities/
    agent/root/surface) so the discover capability can project the
    ranker's float score onto the stable int ``DiscoveryMatch.score``
    field without a cross-capability import (AES201).
    """
    return max(0, round(score * BM25F_SCORE_SCALE))


def sanitize_skill_name(raw: str, fallback: str) -> str:
    """Convert frontmatter name into a safe directory name (prevents path traversal)."""
    raw = (raw or "").strip().replace("\\", "/")
    raw = posixpath.basename(raw)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-")
    if not name:
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", fallback).strip(".-") or "skill"
    return name[:64]


@dataclass(frozen=True)
class CatalogReport:
    """The result of rebuilding ``catalog.json``."""

    path: Path
    skills: int
    categories: int


@dataclass(frozen=True)
class CatalogCheckResult:
    """The result of ``catalog --check`` (never writes)."""

    in_sync: bool
    diff_lines: tuple[str, ...] = ()
    message: str = ""


@dataclass(frozen=True)
class BM25FHit:
    """A ranked result row plus which logical fields contributed to its score."""

    score: float
    row: object
    matched_fields: tuple[str, ...]


@dataclass(frozen=True)
class _Row:
    """One catalog row the discover capability scores."""

    skill: str
    category: str
    description: str
    path: str
    when_to_use: str = ""


@dataclass(frozen=True)
class DiscoveryMatch:
    """One scored discovery row.

    ``matched_fields`` carries the logical field names that contributed
    to this match (e.g. ``("name", "when_to_use")``) — empty on the
    tree-scan fallback or when no field match was recorded.
    """

    skill: str
    category: str
    description: str
    path: str
    score: int
    matched_fields: tuple[str, ...] = ()
    when_to_use: str = ""

    def as_dict(self) -> dict[str, object]:
        """The legacy match projection, in legacy key order."""
        return {
            "skill": self.skill,
            "category": self.category,
            "description": self.description,
            "path": self.path,
            "score": self.score,
            "matched_fields": list(self.matched_fields),
            "when_to_use": self.when_to_use,
        }


@dataclass(frozen=True)
class DiscoveryResult:
    """Discovery matches plus the drift-fallback warning state.

    ``warning`` mirrors today's JSON ``warning`` key (empty on the happy
    path); ``warning_detail`` carries the legacy ``  reason: ...`` stderr
    line's detail so the surface can reproduce it verbatim.
    """

    matches: tuple[DiscoveryMatch, ...] = ()
    warning: str = ""
    warning_detail: str = ""


__all__ = [
    "BM25FHit",
    "CatalogCheckResult",
    "CatalogReport",
    "CategoryName",
    "DiscoveryMatch",
    "DiscoveryResult",
    "ErrorMessage",
    "SkillContent",
    "SkillDescription",
    "SkillName",
    "SkillRecord",
    "SkillsJsonPayload",
    "_Row",
    "map_to_legacy_score",
    "sanitize_skill_name",
]
