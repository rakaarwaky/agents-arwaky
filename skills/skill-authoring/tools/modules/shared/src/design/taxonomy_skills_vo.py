"""Skills taxonomy value objects (AES taxonomy layer, design domain).

The design-domain ``_vo`` module. It carries:

* the published rule shape (``IssueType``, ``Rule``, the ``RULES`` table,
  and the ``rule``/``is_valid_skill_name``/``issue_message`` helpers);
* the authoring result/mutation VOs (``ValidationReport``,
  ``MutationPlan``, ...);
* the lifecycle telemetry/ledger VOs (``TelemetryRow``, ``LedgerEntry``);
* the lifecycle config VO.

Cross-domain shared VOs (``SkillRecord``, ``CatalogReport``,
``DiscoveryResult``, ...) live in
``shared.src.common.taxonomy_common_vo``; this module defines only
design-domain types.

Everything here is pure data except ``load_lifecycle_config``, which
reads the pack-root config file and overlays it over the dataclass
defaults. No imports from capabilities, agent, root, or surface layers.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from shared.src.common.taxonomy_common_constant import (
    NAME_MAX,
    NAME_MIN,
    NAME_RE,
)
from shared.src.design.taxonomy_skills_constant import (
    CITATIONS,
    SUMMARIES,
)

if TYPE_CHECKING:
    # ``Issue`` lives in the entity module, which imports ``IssueType``
    # from here. The annotation is a string (PEP 563), so the runtime
    # import stays one-directional: entity -> vo.
    from shared.src.design.taxonomy_skills_entity import Issue

logger = logging.getLogger(__name__)

# ─── Issue taxonomy ────────────────────────────────────────────────────


#: Exactly the 12 strings ``librarian.py`` ``validate_library`` emits.
#: The ``validate`` command must keep emitting these verbatim, so they
#: live here, not in two places.
class IssueType(str, Enum):
    """The closed set of validation issue types."""

    NAME_MISMATCH = "name-mismatch"
    INVALID_SKILL_NAME = "invalid-skill-name"
    MISSING_DESCRIPTION = "missing-description"
    INVALID_DESCRIPTION_CHARACTERS = "invalid-description-characters"
    DESCRIPTION_TOO_LONG = "description-too-long"
    INVALID_PLACEMENT = "invalid-placement"
    TOO_DEEP = "too-deep"
    DUPLICATE_SKILL_NAME = "duplicate-skill-name"
    DUPLICATE_DESCRIPTION = "duplicate-description"
    MISSING_CATEGORY_DESCRIPTION = "missing-category-description"
    EMPTY_CATEGORY_DESCRIPTION = "empty-category-description"
    EMPTY_CATEGORY = "empty-category"
    REFERENCE_NOT_LINKED = "reference-not-linked"


#: Rule IDs are stable identifiers the skill bodies and the generated
#: ``skill-rules.md`` link against; only the member order of this mapping
#: defines the doc's section order.
RULE_IDS: Final = {
    "name-mismatch": IssueType.NAME_MISMATCH,
    "name-format": IssueType.INVALID_SKILL_NAME,
    "description-present": IssueType.MISSING_DESCRIPTION,
    "description-characters": IssueType.INVALID_DESCRIPTION_CHARACTERS,
    "description-length": IssueType.DESCRIPTION_TOO_LONG,
    "skill-placement": IssueType.INVALID_PLACEMENT,
    "category-depth": IssueType.TOO_DEEP,
    "unique-skill-name": IssueType.DUPLICATE_SKILL_NAME,
    "unique-description": IssueType.DUPLICATE_DESCRIPTION,
    "category-description-present": IssueType.MISSING_CATEGORY_DESCRIPTION,
    "category-description-nonempty": IssueType.EMPTY_CATEGORY_DESCRIPTION,
    "category-nonempty": IssueType.EMPTY_CATEGORY,
    "references-linked": IssueType.REFERENCE_NOT_LINKED,
}

#: Verbatim message templates. Fields are exactly the ones
#: ``librarian.py`` interpolates; ``{}`` are bound by keyword by the same
#: callsite shape as the original code so messages stay byte-identical.
ISSUE_MESSAGES: Final = {
    IssueType.NAME_MISMATCH: (
        "Frontmatter name '{name}' does not match directory '{dir}'."
    ),
    IssueType.INVALID_SKILL_NAME: (
        "Directory name must be lowercase a-z, 0-9, hyphens, 2-64 chars, "
        "no leading/trailing hyphen or double hyphen."
    ),
    IssueType.MISSING_DESCRIPTION: "SKILL.md description is missing.",
    IssueType.INVALID_DESCRIPTION_CHARACTERS: (
        "Description contains <, >, or double quote characters."
    ),
    IssueType.DESCRIPTION_TOO_LONG: (
        "Description is {length} chars; max is {max_len}."
    ),
    IssueType.INVALID_PLACEMENT: (
        "SKILL.md is directly under a category; expected category/skill/SKILL.md."
    ),
    IssueType.TOO_DEEP: (
        "SKILL.md is nested deeper than category/skill/SKILL.md."
    ),
    IssueType.DUPLICATE_SKILL_NAME: "Skill name '{name}' appears in: {paths}.",
    IssueType.DUPLICATE_DESCRIPTION: "Identical description appears in: {paths}.",
    IssueType.MISSING_CATEGORY_DESCRIPTION: "DESCRIPTION.md is missing.",
    IssueType.EMPTY_CATEGORY_DESCRIPTION: "DESCRIPTION.md has no description.",
    IssueType.EMPTY_CATEGORY: "Category has no skills.",
    IssueType.REFERENCE_NOT_LINKED: "Unlinked reference file(s): {paths}",
}


#: Severity of a rule. Every check the validator performs today fails the
#: skill outright, so all 13 rules are ERROR; the WARN level exists for
#: future soft rules and is part of the published interface so the docs
#: renderer does not need to change when the first soft rule lands.
class Level(str, Enum):
    """Rule severity."""

    ERROR = "error"
    WARN = "warn"


@dataclass(frozen=True)
class Rule:
    """One named constraint from the executable SSOT.

    ``id`` is the kebab-case identifier the rest of the pack links to
    (``rule("name-format")`` is how ``validate`` reads the detail);
    ``level`` is the severity; ``summary`` is the
    one-line form shown in the skill-rules reference doc; ``detail_md`` is the
    verbatim message template the validator emits, so the reference doc
    ``skill-rules.md`` cannot disagree with the executable rule;
    ``why`` is the loader citation (empty when no real citation exists).
    """

    id: str
    issue: IssueType
    level: Level
    summary: str
    detail_md: str
    why: str


#: The typed Rule/IssueType taxonomy: one Rule per IssueType. ``detail_md``
#: is the verbatim template from ``ISSUE_MESSAGES`` (the two maps can never
#: diverge: ``issue_message`` and the docs renderer both read it through
#: here), and ``why`` cites the loader file each constraint was first read
#: from. Rules whose constraint was inferred from the validator's own
#: behavior rather than from a written source carry an empty ``why``
#: rather than an invented citation.
RULES: Final = tuple(
    Rule(
        id=rule_id,
        issue=issue_type,
        level=Level.ERROR,
        summary=SUMMARIES[rule_id],
        detail_md=ISSUE_MESSAGES[issue_type],
        why=CITATIONS[rule_id],
    )
    for rule_id, issue_type in RULE_IDS.items()
)

_RULES_BY_ID: Final = {r.id: r for r in RULES}


def rule(rule_id: str) -> Rule:
    """The lookup: ``rule("name-format").detail_md`` is the message
    ``validate`` emits. A typo'd id fails loudly (KeyError) rather than
    silently falling back to a generic message."""
    return _RULES_BY_ID[rule_id]


def is_valid_skill_name(name: str) -> bool:
    """The name-format predicate for skill directory names.

    ``NAME_RE`` match AND no double hyphen AND 2-64 chars.
    """
    return bool(NAME_RE.match(name)) and "--" not in name and NAME_MIN <= len(name) <= NAME_MAX


def issue_message(issue_type: IssueType, **fields: Any) -> str:
    """Render the verbatim message for an issue type with the given fields."""
    return ISSUE_MESSAGES[issue_type].format(**fields)


# ─── Authoring value objects ───────────────────────────────────────────


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


# ─── Lifecycle value objects ───────────────────────────────────────────


@dataclass(frozen=True)
class TelemetryRow:
    """One telemetry row: the auto-transition source of truth."""

    name: str
    state: str
    pinned: bool
    created_by: str | None
    created_at: str | None
    first_seen_at: str | None
    last_activity_at: str | None
    archived_at: str | None
    views: int
    uses: int
    activity_window_start: str | None
    locked: bool = False


@dataclass(frozen=True)
class LedgerEntry:
    """One append-only audit-ledger row."""

    id: str
    ts: str
    actor: str
    action: str
    skill: str
    before: tuple[dict[str, Any], ...] = ()
    after: tuple[dict[str, Any], ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)


# ─── Lifecycle config ──────────────────────────────────────────────────


@dataclass(frozen=True)
class LifecycleConfig:
    """Defaults for skill lifecycle management."""

    enabled: bool = True
    interval_hours: int = 168
    min_idle_hours: int = 2
    stale_after_days: int = 14
    archive_after_days: int = 30
    consolidate: bool = False
    backup_enabled: bool = True
    backup_keep: int = 2
    archive_ttl_days: int = 30
    pause: bool = False


def load_lifecycle_config(pack_root: Path | None = None) -> LifecycleConfig:
    """Return the global lifecycle config (single source of truth — no JSON file)."""

    return LifecycleConfig()


__all__ = [
    "ISSUE_MESSAGES",
    "RULES",
    "RULE_IDS",
    "IssueType",
    "LedgerEntry",
    "LifecycleConfig",
    "LintReport",
    "Level",
    "MutationOutcome",
    "MutationPlan",
    "MutationStep",
    "NewCategoryPlan",
    "Rule",
    "SkillCreatePlan",
    "TelemetryRow",
    "ValidationReport",
    "is_valid_skill_name",
    "issue_message",
    "load_lifecycle_config",
    "rule",
]