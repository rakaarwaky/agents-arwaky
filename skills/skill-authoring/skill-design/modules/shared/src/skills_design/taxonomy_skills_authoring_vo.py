"""Authoring value objects for the skills feature (AES taxonomy layer).

Typed returns for every authoring capability: validation reports,
catalog rows/rebuild/check results, discovery results, mutation plans
and outcomes, and the
trace-pipeline report VOs. Pure data — no I/O and no imports from
utility, capabilities, agent, root, or surface layers. The surface
projects these to the legacy JSON shapes.

The trace report VOs (``UsageReport``/``PhrasesReport``) compose
primitives defined in ``taxonomy_skills_vo.py`` (which re-exports the
class objects from this module); the re-export keeps the two files
mutually importable without a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shared.src.skills_design.taxonomy_skills_entity import Issue

__all__ = [
    "CatalogCheckResult",
    "CatalogReport",
    "CatalogRow",
    "DiscoveryMatch",
    "DiscoveryResult",
    "LintReport",
    "MutationOutcome",
    "MutationPlan",
    "MutationStep",
    "NewCategoryPlan",
    "PhrasesReport",
    "SkillCreatePlan",
    "UsageReport",
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
        """The ``catalog.json`` the report names."""
        return self.catalog

    def summary(self) -> str:
        """The one-line observability summary: issues / skills / categories."""
        return (
            f"{self.issue_count} issues / {self.skills} skills / "
            f"{self.categories} categories"
        )


@dataclass(frozen=True)
class LintReport:
    """The combined result of the lint scan (13-rule checks + weed report)."""

    skills_root: Path
    issues: tuple[Issue, ...] = ()
    weed_lines: tuple[str, ...] = ()
    skills: int = 0
    categories: int = 0
    unfiltered_issues: tuple[Issue, ...] = ()
    unfiltered_weed_lines: tuple[str, ...] = ()

    @property
    def issue_count(self) -> int:
        """Total issues: filtered validator issues + filtered weed lines."""
        return len(self.issues) + len(self.weed_lines)

    @property
    def unfiltered_issue_count(self) -> int:
        """Total issues before category filtering (drives the exit code)."""
        return len(self.unfiltered_issues) + len(self.unfiltered_weed_lines)

    def summary(self) -> str:
        """The one-line observability summary: issues / skills / categories."""
        return (
            f"{self.unfiltered_issue_count} issues / {self.skills} skills / "
            f"{self.categories} categories"
        )


@dataclass(frozen=True)
class CatalogRow:
    """One skill row of ``catalog.json`` (the legacy 4-field projection)."""

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
class SkillCreatePlan:
    """The planned skill creation (dry-run default; ``--apply`` writes).

    ``already_exists`` records that the skill directory was found, so the
    handler can skip the apply. The frontmatter fields are the exact keys
    the validator enforces (``name``, ``description``, ``when-to-use``,
    ``argument-hint``); the ``body`` is the markdown content after the
    frontmatter block.
    """

    skill: str
    category: str
    description: str = ""
    when_to_use: str = ""
    argument_hint: str = ""
    body: str = ""
    directory: Path = Path()
    skill_md: Path = Path()
    already_exists: bool = False
    root: Path | None = None


@dataclass(frozen=True)
class UsageReport:
    """The skills-only usage material the LLM reads from ``usage.json``.

    One ``SkillUsageItem`` per loaded skill plus the ``unused_loaded``
    verdict the unlearn step filters on.
    """

    kept_sessions: int
    items: tuple[SkillUsageItem, ...] = ()
    unused_loaded: tuple[str, ...] = ()


@dataclass(frozen=True)
class PhrasesReport:
    """Repeated exact prompts, repeated instruction lines, and prompt stems.

    Counts are distinct sessions; single-turn sessions repeated 3+ times
    are excluded as likely automation. The surface projects this to the
    legacy ``phrases.json`` shape.
    """

    exact_prompts: tuple[PhraseRow, ...] = ()
    stems: tuple[PhraseRow, ...] = ()
    repeated_instruction_lines: tuple[PhraseRow, ...] = ()

# Runtime import of the two primitives this module's annotations reference
# (``PhraseRow``, ``SkillUsageItem``). Placed at the bottom because
# ``taxonomy_skills_vo`` re-exports this module's class objects — importing
# it back at the top would cycle. The import lands after this module's
# class definitions, so the primitives (and the module's own classes) are
# both loaded by the time ``get_type_hints`` evaluates the string
# annotations above. AES403-safe: imports only ``modules.shared`` types,
# no I/O.
from shared.src.skills_design.taxonomy_skills_vo import (
    PhraseRow,
    SkillUsageItem,
)
