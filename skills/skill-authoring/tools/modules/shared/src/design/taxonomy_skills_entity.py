"""Skills-domain entities (AES taxonomy layer, design domain).

Identity-bearing domain records produced by the authoring tree walk and
the validator. Pure data: no I/O, no imports from utility, capabilities,
agent, root, or surface layers.

Cross-domain shared entities (``SkillEntry``, ``CategorySummary``) live
in ``shared.src.common.taxonomy_common_entity``; this module defines
only the design-domain ``Issue`` record.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.src.design.taxonomy_skills_vo import IssueType

__all__ = [
    "Issue",
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