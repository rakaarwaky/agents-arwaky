"""Skills-domain entities (AES taxonomy layer).

Identity-bearing domain records produced by the authoring tree walk and
the validator. Pure data: no I/O, no imports from utility, capabilities,
agent, root, or surface layers.

Shared entities consumed by more than one module domain live in
``shared.src.common.taxonomy_common_entity``; this module re-exports them
so existing imports keep working.
"""

from __future__ import annotations

from dataclasses import dataclass

# Re-export shared entities from the common layer (single source of truth).
from shared.src.common.taxonomy_common_entity import (
    CategorySummary,
    SkillEntry,
)
from shared.src.design.taxonomy_skills_vo import IssueType

__all__ = [
    "CategorySummary",
    "Issue",
    "SkillEntry",
]


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
