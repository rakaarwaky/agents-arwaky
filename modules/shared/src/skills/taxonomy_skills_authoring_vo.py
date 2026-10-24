"""Authoring value objects for the skills feature (AES taxonomy layer).

Typed returns for every authoring capability: validation reports,
catalog rows/rebuild/check results, discovery results, mutation plans
and outcomes, merge plans, and the rendered rules document. Pure data —
no I/O and no imports from utility, capabilities, agent, root, or
surface layers. The surface projects these to the legacy JSON shapes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from modules.shared.src.skills.taxonomy_skills_entity import Issue

__all__ = [
    "CatalogCheckResult",
    "CatalogReport",
    "CatalogRow",
    "DiscoveryMatch",
    "DiscoveryResult",
    "MergePlan",
    "MutationOutcome",
    "MutationPlan",
    "MutationStep",
    "NewCategoryPlan",
    "RulesDocument",
    "ValidationReport",
]


@dataclass(frozen=True)
class ValidationReport:
    """The unfiltered result of the 13 validation checks."""

    skills_root: Path
    catalog: Path
    issues: tuple[Issue, ...] = ()
    skills: int = 0
    categories: int = 0

    @property
    def issue_count(self) -> int:
        """The unfiltered issue total (drives the exit code)."""
        return len(self.issues)

    @property
    def catalog_path(self) -> Path:
        """The ``CATALOG.md`` the report names."""
        return self.catalog

    def summary(self) -> str:
        """The one-line observability summary: issues / skills / categories."""
        return (
            f"{self.issue_count} issues / {self.skills} skills / "
            f"{self.categories} categories"
        )


@dataclass(frozen=True)
class CatalogRow:
    """One parsed ``## Skills`` row of ``CATALOG.md``."""

    skill: str
    category: str
    description: str
    path: str

    def as_dict(self) -> dict[str, str]:
        """The legacy row projection, in legacy key order."""
        return {
            "skill": self.skill,
            "category": self.category,
            "description": self.description,
            "path": self.path,
        }


@dataclass(frozen=True)
class CatalogReport:
    """The result of rebuilding ``CATALOG.md``."""

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
class DiscoveryMatch:
    """One scored discovery row."""

    skill: str
    category: str
    description: str
    path: str
    score: int

    def as_dict(self) -> dict[str, object]:
        """The legacy match projection, in legacy key order."""
        return {
            "skill": self.skill,
            "category": self.category,
            "description": self.description,
            "path": self.path,
            "score": self.score,
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


@dataclass(frozen=True)
class MutationStep:
    """One planned file operation.

    ``description`` is the legacy report line for the step; ``action``
    names the operation the mutator executes (``rewrite-name``,
    ``create-description``); ``value`` carries the expected name or the
    description text the step would write.
    """

    action: str
    description: str
    source: Path | None = None
    destination: Path | None = None
    value: str = ""


@dataclass(frozen=True)
class MutationPlan:
    """A pure, pre-apply description of a mutation (never writes)."""

    kind: str
    source: Path | None = None
    destination: Path | None = None
    steps: tuple[MutationStep, ...] = ()
    lines: tuple[str, ...] = ()
    already_in_category: bool = False
    root: Path | None = None


@dataclass(frozen=True)
class MutationOutcome:
    """The post-apply result: the step lines the mutation performed."""

    applied: tuple[str, ...] = ()
    message: str = ""


@dataclass(frozen=True)
class NewCategoryPlan:
    """A planned category creation.

    ``will_write`` is the plan-time prediction (an existing
    ``DESCRIPTION.md`` without ``--force`` is kept); ``created`` records
    what an apply actually did.
    """

    name: str
    description: str = ""
    directory: Path = Path()
    description_file: Path = Path()
    will_write: bool = False
    created: bool = False
    root: Path | None = None


@dataclass(frozen=True)
class MergePlan:
    """The read-only merge plan ``skill-lifecycle`` executes."""

    survivor: str
    absorbed: str
    survival_reason: str
    moves: tuple[tuple[str, str], ...] = ()
    rewrites: tuple[Mapping[str, str], ...] = ()
    category_after: str = ""
    empty_category_after: str | None = None


@dataclass(frozen=True)
class RulesDocument:
    """The rendered SSOT: the markdown doc and the one-line-per-rule summary."""

    markdown: str
    summary: str
    rule_count: int = 0
