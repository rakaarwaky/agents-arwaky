"""Skill-tree taxonomy VOs (AES taxonomy layer).

The single taxonomy home for the two discovery row shapes shared between
the catalog capability and the BM25F ranker: ``skill_entries`` /
``category_summaries`` produce ``SkillEntry`` and ``CategorySummary``
rows (from the design-domain entity module), and the free-function
wrappers here keep the import direction one-way — the discovery
taxonomy imports design entities, never capabilities or agents.

Re-exported by ``utility_skills_tree`` so capability-layer consumers
keep their imports working.
"""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from shared.src.discovery.utility_skills_core import (
    category_dirs,
    category_summaries,
    clean_one_line,
    parse_frontmatter,
    skill_entries,
)
from shared.src.design.taxonomy_skills_entity import (
    CategorySummary,
    SkillEntry,
)

__all__ = [
    "CategorySummary",
    "SkillEntry",
    "category_dirs",
    "category_summaries",
    "parse_frontmatter",
    "skill_entries",
]
