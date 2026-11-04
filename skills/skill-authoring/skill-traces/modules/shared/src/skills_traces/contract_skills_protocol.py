"""Skills traces contract protocols (AES contract layer).

Two seams for the trace-learning lifecycle:
  - ISkillsTraceScanProtocol: scan sessions, build usage, mine phrases, materialize
  - ISkillsTraceStateProtocol: status machine, trash, decisions, wait, restrict, dispatch

Capabilities implement these; the composition root injects them into the agent.
Capabilities never import one another: dependencies cross seams as protocols,
wired by the root.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from shared.src.skills_traces.taxonomy_skills_authoring_vo import (
    PhrasesReport,
    UsageReport,
)
from shared.src.skills_traces.taxonomy_skills_constant import (
    TRACE_COLLECT_MIN_TURNS,
)
from shared.src.skills_traces.taxonomy_skills_entity import (
    CategorySummary,
    Issue,
    SkillEntry,
)
from shared.src.skills_traces.taxonomy_skills_rule_vo import (
    CategoryName,
    IssueType,
    Level,
    Rule,
    SkillName,
)
from shared.src.skills_traces.taxonomy_skills_vo import (
    GrokHome,
    ScanResult,
    TraceDecision,
    TraceRunDir,
    TraceRunName,
    TraceStateDispatchResult,
    TraceStateStatus,
)


class ISkillsTraceScanProtocol(ABC):
    """Scan sessions, build skills-only usage, mine repeated phrases, materialize."""

    @abstractmethod
    def scan_sessions(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        days: int = 0,
        since_last: bool = False,
        min_turns: int = 1,
        limit: int = 0,
        include_headless: bool = False,
        include_subagents: bool = False,
    ) -> ScanResult:
        """Scan the session tree with the filters and return a ``ScanResult``.

        Writes ``manifest.json`` plus ``sessions/*.json`` into *run_dir*
        and returns the kept records plus the scan counters
        (``sessions_seen``, ``dropped``) as a VO.
        """
        ...

    @abstractmethod
    def build_usage(self, grok_home: GrokHome, run_dir: TraceRunDir) -> UsageReport:
        """Return the skills-only usage: hit counts, sessions, last_used, unused_loaded."""
        ...

    @abstractmethod
    def build_phrases(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        min_sessions: int = TRACE_COLLECT_MIN_TURNS,
    ) -> PhrasesReport:
        """Mine repeated exact prompts, prompt stems, and repeated instruction lines.

        Reads the session records written to *run_dir*; returns
        distinct-session counts with single-turn automation excluded.
        """
        ...

    def materialize(
        self, grok_home: GrokHome, run_dir: TraceRunDir
    ) -> tuple[UsageReport, PhrasesReport]:
        """Build usage + phrases for *run_dir* and write
        ``usage.json`` + ``phrases.json`` into it.

        Returns the two reports so the agent can echo them in the result.
        """


class ISkillsTraceStateProtocol(ABC):
    """Trace-learning lifecycle: status machine, trash, decisions, wait, restrict, dispatch."""

    @abstractmethod
    def set_status(
        self, grok_home: GrokHome, run_dir: TraceRunDir, status: TraceStateStatus
    ) -> TraceStateStatus:
        """Record *status* for the pending run; ``done`` stamps last_completed."""
        ...

    @abstractmethod
    def get_status(self, grok_home: GrokHome) -> TraceStateStatus:
        """Return the current pending status."""
        ...

    @abstractmethod
    def trash(
        self, grok_home: GrokHome, run_name: TraceRunName, paths: Sequence[str]
    ) -> tuple[str, ...]:
        """Move the validated paths into ``learn/trash/<run_name>``."""
        ...

    @abstractmethod
    def decide(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        decision: TraceDecision,
    ) -> TraceDecision:
        """Append one decision line to ``learn/decisions.jsonl`` and return it."""
        ...

    @abstractmethod
    def wait(
        self,
        grok_home: GrokHome,
        run_dir: TraceRunDir,
        timeout_min: int = 90,
        phase_stall_min: int = 60,
        report_stall_min: int = 45,
    ) -> TraceStateStatus:
        """Block until the run dir holds ``report.md`` + ``actions.json``."""
        ...

    def restrict(self, paths: Sequence[str]) -> tuple[str, ...]:
        """chmod 0600 where the OS supports it; silently skip what it cannot."""

    def dispatch(
        self,
        grok_home: str,
        run_dir: str,
        action: str,
        flags: Mapping[str, str],
    ) -> TraceStateDispatchResult:
        """Route one trace-state sub-action through this capability."""


# ── Internal seams end ──


__all__ = [
    "CategorySummary",
    "Issue",
    "ISkillsTraceScanProtocol",
    "ISkillsTraceStateProtocol",
    "IssueType",
    "Level",
    "Rule",
    "SkillEntry",
    "SkillName",
]
