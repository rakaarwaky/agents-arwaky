"""Shared-kernel entities for the skills domain (AES common layer).

Identity-bearing domain records produced by the authoring tree walk and
the validator, shared across more than one module domain. Pure data:
no I/O, no imports from utility, capabilities, agent, root, or surface
layers.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.src.common.taxonomy_common_vo import SkillName  # noqa: F401


__all__ = [
    "CategorySummary",
    "SkillEntry",
]


@dataclass(frozen=True)
class SkillEntry:
    """One discoverable skill at ``category/skill``.

    Fields mirror the dict the original ``skill_entries`` produced, so
    callers can index them identically. ``path`` is the
    ``category/skill`` identity string used in every report.
    """

    skill: str
    frontmatter_name: str
    category: str
    description: str
    when_to_use: str
    path: str


@dataclass(frozen=True)
class CategorySummary:
    """One category folder: description state and skill count."""

    category: str
    description: str
    description_file_exists: bool
    skill_count: int
