"""Skills taxonomy value objects (AES taxonomy layer).

Pure data + helpers for the skills feature: the read-side VOs
(``SkillQuery``/``SkillRecord``/...), the request/result envelope the
surface and agent exchange, the exit-code contract, and the re-exported
rule SSOT (defined in ``taxonomy_skills_constant`` so the rule table's
dependencies stay acyclic).

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import NewType

from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    CatalogCheckResult,
    CatalogReport,
    DiscoveryMatch,
    MergePlan,
    MutationOutcome,
    MutationPlan,
    NewCategoryPlan,
    ValidationReport,
)
from modules.shared.src.skills.taxonomy_skills_constant import (
    ISSUE_MESSAGES,
    RULES,
    IssueType,
    Level,
    Rule,
    is_valid_skill_name,
    issue_message,
    rule,
)
from modules.shared.src.skills.taxonomy_skills_entity import (
    CategorySummary,
    Issue,
    SkillEntry,
)

SkillQuery = NewType("SkillQuery", str)
"""A skill name / identifier to look up in the pack."""

SkillContent = NewType("SkillContent", str)
"""Raw SKILL.md text returned by a read."""

SkillDescription = NewType("SkillDescription", str)
"""One-line description extracted from SKILL.md frontmatter."""

SkillsRoot = NewType("SkillsRoot", Path)
"""An explicit skills root; ``None`` on a request means 'use the default'."""


class SkillsOp(StrEnum):
    """Every operation the skills aggregate understands."""

    LIST = "list"
    SHOW = "show"
    VALIDATE = "validate"
    CATALOG = "catalog"
    DISCOVER = "discover"
    WEED = "weed"
    REPAIR = "repair"
    MOVE = "move"
    ARCHIVE = "archive"
    NEW_CATEGORY = "new-category"
    MERGE_PLAN = "merge-plan"
    RULES = "rules"


class SkillsExitCode(IntEnum):
    """Single source of truth for the CLI exit-code contract.

    The surface maps ``SkillsResult.exit_code`` against this enum;
    capabilities never emit exit codes themselves — they set them on the
    errors they raise, and the agent derives them from check results.
    """

    CLEAN = 0
    ISSUES_FOUND = 1
    USAGE_ERROR = 2
    CATALOG_DRIFT = 3


@dataclass(frozen=True)
class SkillRecord:
    """One discoverable skill in the pack."""

    name: str
    description: SkillDescription
    path: Path


@dataclass(frozen=True)
class SkillsRequest:
    """Input for one skills operation.

    ``op`` selects the capability; ``query`` carries the skill name or the
    search query; ``root`` overrides the default pack root (explicit beats
    derived); ``apply`` is the only path to a write; ``flags`` carries the
    per-op positional/optional strings (``category``, ``target``,
    ``limit``, ``force``, ...).
    """

    op: SkillsOp = SkillsOp.LIST
    query: SkillQuery = field(default_factory=lambda: SkillQuery(""))
    root: SkillsRoot | None = None
    apply: bool = False
    json: bool = False
    description: str = ""
    flags: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SkillsResult:
    """Response to a skills operation.

    ``exit_code`` is the CLI contract: 0 clean / 1 issues / 2 usage /
    3 catalog drift. Payload fields are populated per op; the surface
    renders them and never reaches back into a capability.
    """

    ok: bool
    op: SkillsOp = SkillsOp.LIST
    exit_code: int = 0
    message: str = ""
    records: tuple[SkillRecord, ...] = ()
    content: SkillContent | None = None
    report: ValidationReport | None = None
    catalog: CatalogReport | None = None
    check: CatalogCheckResult | None = None
    matches: tuple[DiscoveryMatch, ...] = ()
    plan: MutationPlan | None = None
    outcome: MutationOutcome | None = None
    new_category: NewCategoryPlan | None = None
    merge: MergePlan | None = None
    document: str | None = None
    lines: tuple[str, ...] = ()
    warning: str | None = None
    root: Path | None = None


__all__ = [
    "ISSUE_MESSAGES",
    "RULES",
    "CatalogCheckResult",
    "CatalogReport",
    "CategorySummary",
    "DiscoveryMatch",
    "Issue",
    "IssueType",
    "Level",
    "MergePlan",
    "MutationOutcome",
    "MutationPlan",
    "NewCategoryPlan",
    "Rule",
    "SkillContent",
    "SkillDescription",
    "SkillEntry",
    "SkillQuery",
    "SkillRecord",
    "SkillsExitCode",
    "SkillsOp",
    "SkillsRequest",
    "SkillsResult",
    "SkillsRoot",
    "ValidationReport",
    "is_valid_skill_name",
    "issue_message",
    "rule",
]
