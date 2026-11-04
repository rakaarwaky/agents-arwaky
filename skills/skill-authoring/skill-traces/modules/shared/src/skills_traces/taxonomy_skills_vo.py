"""Skills taxonomy value objects (AES taxonomy layer).

Pure data + helpers for the skills feature: the read-side VOs
(``SkillRecord``/...), the trace-pipeline VOs, and the re-exported rule
SSOT (defined in ``taxonomy_skills_rule_vo.py`` so the rule table's
dependencies stay acyclic). The request envelope
(``SkillsRequest``/``SkillsOp``/``SkillQuery``/``SkillsRoot``) lives in
``taxonomy_skills_request.py`` and the response envelope
(``SkillsResult``/``SkillsExitCode``) lives in
``taxonomy_skills_response.py``; both are re-exported here (from
``SkillQuery``/``SkillsRoot`` at the top and the two envelopes at the
bottom) so existing imports keep working. The trace report VOs
(``UsageReport``/``PhrasesReport``) live in
``taxonomy_skills_authoring_vo.py`` over the primitives defined here.

No I/O, no imports from utility/capabilities/agent/root/surface layers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import NewType

from shared.src.skills_traces.taxonomy_skills_request import SkillQuery, SkillsRoot

# Every other primitive below (``SkillContent``, ``SkillRecord``, the trace
# VOs, ...) is re-exported back into the request/response envelope modules
# after its definition, so the envelope modules never import this module at
# runtime — no cycle in either import order.
SkillContent = NewType("SkillContent", str)
"""Raw SKILL.md text returned by a read."""

SkillDescription = NewType("SkillDescription", str)
"""One-line description extracted from SKILL.md frontmatter."""

ErrorMessage = NewType("ErrorMessage", str)
"""A formatted error message for skill-domain exceptions."""

DiffLines = NewType("DiffLines", tuple[str, ...])
"""A sequence of diff lines for catalog drift errors."""

SkillsJsonPayload = NewType("SkillsJsonPayload", Mapping[str, object])
"""The pure-data JSON list of global skills (``SkillsLister.list_skills_json``).

One entry per skill (``name``, ``source``, ``path``, ``loaded``); the
source is the repo pack only. A pure-data dict, so it never touches I/O.
"""

GrokHome = NewType("GrokHome", str)
"""The ``$GROK_HOME`` directory the trace-learning lifecycle reads and writes."""

TraceRunDir = NewType("TraceRunDir", str)
"""The run directory one trace scan writes into (``report.md``, ``sessions/``)."""

TraceRunName = NewType("TraceRunName", str)
"""A single path component naming one trace run (trash/restrict target)."""


class TraceStateStatus(StrEnum):
    """The trace-learning lifecycle status of a pending run.

    ``collected`` → ``running`` → ``report_ready`` → ``curating`` → ``done``
    is the lifecycle machine driven by ``set_status``. ``PHASE_STALL``,
    ``REPORT_STALL``, and ``DEADLINE`` are the distinct terminal outcomes of
    ``wait`` (the surface maps them to exit 4 / 3 / 2 respectively).
    """

    COLLECTED = "collected"
    RUNNING = "running"
    REPORT_READY = "report_ready"
    CURATING = "curating"
    DONE = "done"
    PHASE_STALL = "phase_stall"
    REPORT_STALL = "report_stall"
    DEADLINE = "deadline"


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
class ScanResult:
    """Outcome of one tracker scan: the kept records plus scan counters.

    ``sessions_seen`` is every session directory examined; ``dropped`` maps
    a drop-reason name to its count (the legacy manifest counters, surfaced
    so no consumer re-parses ``manifest.json``).
    """

    records: tuple[TraceSessionRecord, ...]
    sessions_seen: int
    dropped: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class TraceStateDispatchResult:
    """The state capability's single-op projection for the agent's dispatch.

    ``state`` is populated by set/get/clear; ``state_status`` is the
    ``wait`` outcome; ``lines`` carries trash/restrict/decide output.
    """

    state: TraceStateStatus | None = None
    state_status: TraceStateStatus | None = None
    lines: tuple[str, ...] = ()


__all__ = [
    "DiffLines",
    "ErrorMessage",
    "GrokHome",
    "PhraseRow",
    "ScanResult",
    "SkillContent",
    "SkillDescription",
    "SkillQuery",
    "SkillRecord",
    "SkillUsageItem",
    "SkillsJsonPayload",
    "SkillsRoot",
    "TraceDecision",
    "TraceRunDir",
    "TraceRunName",
    "TraceSessionRecord",
    "TraceStateDispatchResult",
    "TraceStateStatus",
]
