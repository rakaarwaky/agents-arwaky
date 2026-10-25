"""Skills-domain entities (AES taxonomy layer).

Identity-bearing domain records produced by the authoring tree walk and
the validator. Pure data: no I/O, no imports from utility, capabilities,
agent, root, or surface layers.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.shared.src.skills.taxonomy_skills_rule_vo import IssueType

__all__ = [
    "CategorySummary",
    "Issue",
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
    path: str


@dataclass(frozen=True)
class CategorySummary:
    """One category folder: description state and skill count."""

    category: str
    description: str
    description_file_exists: bool
    skill_count: int


@dataclass(frozen=True)
class Issue:
    """One validation issue.

    ``type`` is the ``IssueType`` value the report prints, ``message`` the
    verbatim template rendering, and ``path``/``category`` the locator
    (``None`` for library-wide issues).
    """

    type: IssueType
    message: str
    path: str | None = None
    category: str | None = None

    @property
    def locator(self) -> str:
        """The string the report prints after the issue type."""
        return self.path or self.category or "library"