"""Skill-tree walking and frontmatter parsing (AES utility layer).

Re-export shim: the tree-walking functions live in
``utility_skills_core`` (the AES201-documented exception module that
``utility_skills_mutation`` also imports). This module re-exports them
so existing capability-layer consumers keep their imports working.

The ``relpath`` helper lives here directly (single consumer: the
capability layer; not shared with ``utility_skills_mutation``).

Consumers of this shim:
- ``capabilities_discovery_catalog.py`` — imports
  ``category_summaries``, ``skill_entries``.
- ``capabilities_skills_linter.py`` — imports
  ``category_dirs``, ``category_summaries``, ``parse_frontmatter``,
  ``relpath``, ``skill_entries``.
- ``capabilities_skills_mover.py`` — imports ``relpath``.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.discovery.utility_skills_core import (
    category_dirs,
    category_summaries,
    parse_frontmatter,
    skill_entries,
)

__all__ = [
    "category_dirs",
    "category_summaries",
    "parse_frontmatter",
    "relpath",
    "skill_entries",
]


def relpath(path: Path, skills_root: Path) -> str:
    """A skills-root-relative path when possible, else the absolute one."""
    try:
        return str(path.relative_to(skills_root))
    except ValueError:
        return str(path)
