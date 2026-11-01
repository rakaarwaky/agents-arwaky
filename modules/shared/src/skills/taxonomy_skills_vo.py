"""Skills taxonomy value objects (AES taxonomy layer).

Pure data + helpers for the skills feature: the read-side VOs
(``SkillQuery``/``SkillRecord``/...), the request/result envelope the
surface and agent exchange, the exit-code contract, the trace-pipeline
VOs, and the re-exported rule SSOT (defined in
``taxonomy_skills_rule_vo.py`` so the rule table's dependencies stay
acyclic). The trace report VOs (``UsageReport``/``PhrasesReport``) live
in ``taxonomy_skills_authoring_vo.py`` over the primitives defined here.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, NewType

from modules.shared.src.skills.taxonomy_skills_rule_vo import (
    CategoryName,
    SkillName,
    SkillRef,
)

if TYPE_CHECKING:
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

SkillQuery = NewType("SkillQuery", str)
"""A skill name / identifier to look up in the pack."""

SkillContent = NewType("SkillContent", str)
"""Raw SKILL.md text returned by a read."""

SkillDescription = NewType("SkillDescription", str)
"""One-line description extracted from SKILL.md frontmatter."""

ErrorMessage = NewType("ErrorMessage", str)
"""A formatted error message for skill-domain exceptions."""

DiffLines = NewType("DiffLines", tuple[str, ...])
"""A sequence of diff lines for catalog drift errors."""

RulesSummary = NewType("RulesSummary", str)
"""The compact one-line-per-rule summary rendered by the rules renderer."""

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
    TRACE_COLLECT = "trace-collect"
    TRACE_USAGE = "trace-usage"
    TRACE_PHRASES = "trace-phrases"
    TRACE_STATE = "trace-state"


class TraceStateStatus(StrEnum):
    """The trace-learning lifecycle status of a pending run."""

    COLLECTED = "collected"
    RUNNING = "running"
    REPORT_READY = "report_ready"
    CURATING = "curating"
    DONE = "done"


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
class TraceSessionRecord:
    """One compact per-session record the tracker writes to the run dir.

    The fields are the trace-mining raw material (turns, skill loads,
    top dirs touched); the surface projects them to the legacy
    ``sessions/NNNN-<id>.json`` shape.
    """

    id: str
    index: int
    cwd: str
    branch: str = ""
    title: str = ""
    session_kind: str = ""
    updated_at: str = ""
    model: str = ""
    human_turns: int = 0
    turns: tuple[str, ...] = ()
    slash_commands: Mapping[str, int] = field(default_factory=dict)
    skills_loaded: Mapping[str, int] = field(default_factory=dict)
    skill_load_paths: Mapping[str, str] = field(default_factory=dict)
    mcp_servers_used: Mapping[str, int] = field(default_factory=dict)
    tools: Mapping[str, int] = field(default_factory=dict)
    subagent_spawns: int = 0
    workflow_launches: int = 0
    top_dirs_touched: Mapping[str, int] = field(default_factory=dict)
    repeated_single_turn: bool = False
    trace_path: str = ""


@dataclass(frozen=True)
class SkillUsageItem:
    """One loaded skill's usage row (the LLM's disuse verdict input)."""

    name: str
    source: str
    path: str
    loaded: bool
    count: int = 0
    sessions: tuple[str, ...] = ()
    last_used: str | None = None
    in_slash_mru: bool = False


@dataclass(frozen=True)
class PhraseRow:
    """One repeated-phrase row: the normalized text, distinct-session count, occurrences."""

    phrase: str
    sessions: int
    occurrences: int
    session_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TraceDecision:
    """One trace-learning decision line appended to ``decisions.jsonl``."""

    date: str
    run_dir: str
    decision_id: str
    kind: str
    action: str
    target: str
    target_path: str
    decision: str
    undo: str | None = None

    def as_dict(self) -> dict[str, object]:
        """The legacy decision-line projection, in legacy key order.

        Pins the retired ``state.py`` JSON shape; PR 4 wires its consumer.
        """
        return {
            "date": self.date,
            "run_dir": self.run_dir,
            "id": self.decision_id,
            "kind": self.kind,
            "action": self.action,
            "target": self.target,
            "path": self.target_path,
            "decision": self.decision,
            "undo": self.undo,
        }


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
    "CatalogCheckResult",
    "CatalogReport",
    "CategoryName",
    "DiffLines",
    "DiscoveryMatch",
    "ErrorMessage",
    "MergePlan",
    "MutationOutcome",
    "MutationPlan",
    "NewCategoryPlan",
    "PhraseRow",
    "RulesSummary",
    "SkillContent",
    "SkillDescription",
    "SkillName",
    "SkillQuery",
    "SkillRecord",
    "SkillRef",
    "SkillUsageItem",
    "SkillsExitCode",
    "SkillsOp",
    "SkillsRequest",
    "SkillsResult",
    "SkillsRoot",
    "TraceDecision",
    "TraceSessionRecord",
    "TraceStateStatus",
    "ValidationReport",
]

# The authoring VOs above are re-exported for consumers that import the
# whole skills-VO surface from this module. The re-export is lazy so this
# file stays the runtime base of the cycle (``taxonomy_skills_authoring_vo``
# imports the trace primitives from here); the classes land in the
# authoring module, which loads without importing this module's
# re-exports back.
_AUTHORING_REEXPORTS = {
    "CatalogCheckResult",
    "CatalogReport",
    "DiscoveryMatch",
    "MergePlan",
    "MutationOutcome",
    "MutationPlan",
    "NewCategoryPlan",
    "ValidationReport",
}


def __getattr__(name: str):
    if name in _AUTHORING_REEXPORTS:
        from modules.shared.src.skills import taxonomy_skills_authoring_vo

        return getattr(taxonomy_skills_authoring_vo, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")