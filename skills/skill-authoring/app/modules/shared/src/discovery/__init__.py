"""Skills-design shared kernel — discovery layer.

Stateless discovery helpers: tree walking, frontmatter parsing, markdown
string mechanics, cross-process locking, and the discovery loaders that
turn a skills root into skill records and BM25F hits.
"""
from shared.src.discovery.utility_skills_core import (
    category_dirs,
    category_summaries,
    clean_one_line,
    cross_process_lock,
    parse_frontmatter,
    skill_entries,
)

__all__ = [
    "category_dirs",
    "category_summaries",
    "clean_one_line",
    "cross_process_lock",
    "parse_frontmatter",
    "skill_entries",
]
