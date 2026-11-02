"""Skills contract protocols (AES contract layer, ABC traits).

One seam per subsystem the skills agent coordinates: the pack index
(list), the pack reader (show), the validator, the catalog, discovery,
and the mutator, plus the
trace-learning pair (the traces capability and the lifecycle state). Capabilities implement these; the composition root injects them
into the agent.

Capabilities never import one another: where one needs another's data
(the discoverer reads catalog rows), the dependency is expressed as one
of these protocols and wired by the root.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    CatalogCheckResult,
    CatalogReport,
    CatalogRow,
    DiscoveryResult,
    LintReport,
    MutationOutcome,
    MutationPlan,
    NewCategoryPlan,
    PhrasesReport,
    UsageReport,
    ValidationReport,
)
from modules.shared.src.skills.taxonomy_skills_rule_vo import (
    CategoryName,
    SkillName,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    ScanResult,
    SkillContent,
    SkillDescription,
    SkillQuery,
    SkillRecord,
    SkillsRoot,
    TraceDecision,
    TraceStateDispatchResult,
    TraceStateStatus,
)


class ISkillsIndexProtocol(ABC):
    """Read-only listing of the skill pack."""

    @abstractmethod
    def list_skills(self, root: SkillsRoot | None = None) -> Sequence[SkillRecord]:
        """Return one record per skill, sorted by name.

        ``root`` overrides the capability's construction-time pack root
        (explicit beats derived); ``None`` keeps it.
        """
        ...

    def list_skills_json(self, root: SkillsRoot | None = None) -> dict:
        """Return the global-skill JSON list as a pure-data dict.

        One entry per skill (``name``, ``source``, ``path``, ``loaded``);
        the source is the repo pack only. ``SkillsIndexBuilder`` provides
        the real implementation; this default returns ``{}`` for other
        implementors.
        """
        return {}


class ISkillsReaderProtocol(ABC):
    """Read-only content access to one skill's SKILL.md."""

    @abstractmethod
    def show_skill(
        self, query: SkillQuery, root: SkillsRoot | None = None
    ) -> SkillContent | None:
        """Return the raw SKILL.md content for *query*, or None if missing."""
        ...


class ISkillsValidatorProtocol(ABC):
    """The 13-rule validator over a skills tree."""

    @abstractmethod
    def validate(self, root: SkillsRoot) -> ValidationReport:
        """Run the 13 checks over *root*; the report is unfiltered by design."""
        ...


class ISkillsLintProtocol(ABC):
    """Combined lint scan: 13-rule checks + weed report in one pass."""

    @abstractmethod
    def lint(
        self, root: SkillsRoot, category: str | None = None
    ) -> LintReport:
        """Run the full lint over *root*; optionally filter by *category*.

        The lint combines the 13-rule validator (per-skill, category,
        placement, and duplicate checks) with the weed report (duplicate
        skill names, duplicate descriptions, empty categories, missing
        category descriptions). The result is a single ``LintReport``
        carrying both the issues and the weed lines.
        """
        ...


class ISkillsCatalogProtocol(ABC):
    """Render, rebuild, check, and read the tracked ``CATALOG.md``."""

    @abstractmethod
    def rebuild(self, root: SkillsRoot) -> CatalogReport:
        """Walk the tree and rewrite the catalog; return the rendered counts."""
        ...

    @abstractmethod
    def check(self, root: SkillsRoot) -> CatalogCheckResult:
        """Return ``in_sync`` plus the diff lines and summary message.

        On sync: ``in_sync=True``, no diff lines. On drift/missing/
        unparseable/non-round-trip: ``in_sync=False`` with the unified
        diff (or per-cell problems) and a summary message. The agent maps
        ``in_sync=False`` to exit code 3; the surface renders message +
        diff lines to stdout and emits ``{skills_root, in_sync, catalog,
        diff}`` in JSON mode, byte-identical to the legacy command.
        """
        ...

    @abstractmethod
    def load_rows(self, root: SkillsRoot) -> tuple[CatalogRow, ...]:
        """Raise ``CatalogDrift`` rather than repair or fall back — fail closed."""
        ...


class ISkillsDiscovererProtocol(ABC):
    """Query the catalog, with a loud fallback when it drifts."""

    @abstractmethod
    def discover(
        self, query: SkillQuery, root: SkillsRoot, limit: int
    ) -> DiscoveryResult:
        """Search the catalog rows for *query*, returning top *limit* matches.

        Raises ``SkillsUsageError('Query is empty')`` when the query has no
        search tokens (exit 2). On drift, catches ``CatalogDrift`` from
        ``load_rows``, sets the result's warning fields, falls back to the
        live tree scan, and returns matches with exit 0.
        """
        ...


class ISkillsMutatorProtocol(ABC):
    """Plan/apply mechanical library mutations (dry-run by default)."""

    @abstractmethod
    def plan_move(self, skill: SkillName, target: CategoryName, root: SkillsRoot) -> MutationPlan:
        """Resolve a move to another category (pure; no writes)."""
        ...

    @abstractmethod
    def plan_archive(self, skill: SkillName, root: SkillsRoot) -> MutationPlan:
        """Resolve an archive into ``_archive/`` (pure; no writes)."""
        ...

    @abstractmethod
    def plan_repair(self, root: SkillsRoot) -> MutationPlan:
        """Plan the safe mechanical repairs (pure; no writes)."""
        ...

    @abstractmethod
    def plan_weed(self, root: SkillsRoot) -> MutationPlan:
        """Report duplicates, empty categories, and missing descriptions."""
        ...

    @abstractmethod
    def plan_new_category(
        self, name: CategoryName, description: SkillDescription | None, root: SkillsRoot, force: bool
    ) -> NewCategoryPlan:
        """Resolve a category creation (pure; the folder is created on apply)."""
        ...

    @abstractmethod
    def apply(self, plan: MutationPlan) -> MutationOutcome:
        """Execute a repair/move/archive plan; re-checks containment first."""
        ...

    @abstractmethod
    def apply_new_category(self, plan: NewCategoryPlan) -> bool:
        """Create the category and write its description; returns whether it wrote."""
        ...


class ISkillsTracesProtocol(ABC):
    """Scan sessions, build skills-only usage, mine repeated phrases, and drive the trace-learning lifecycle (status machine, trash, decisions, wait)."""

    @abstractmethod
    def scan_sessions(
        self,
        grok_home: str,
        run_dir: str,
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
        (``sessions_seen``, ``dropped``) as a VO — no raw JSON for the
        surface to re-parse.
        """
        ...

    @abstractmethod
    def build_usage(self, grok_home: str, run_dir: str) -> UsageReport:
        """Return the skills-only usage: hit counts, sessions, last_used, unused_loaded."""
        ...

    @abstractmethod
    def build_phrases(self, grok_home: str, run_dir: str) -> PhrasesReport:
        """Mine repeated exact prompts, prompt stems, and repeated instruction lines.

        Reads the session records written to *run_dir*; returns
        distinct-session counts with single-turn automation excluded.
        """
        ...

    # ── Trace-state lifecycle ─────────────────────────────────────────

    @abstractmethod
    def set_status(
        self, grok_home: str, run_dir: str, status: TraceStateStatus
    ) -> TraceStateStatus:
        """Record *status* for the pending run; ``done`` stamps last_completed."""
        ...

    @abstractmethod
    def get_status(self, grok_home: str) -> TraceStateStatus:
        """Return the current pending status.

        ``done``-less pending runs exit 3 (the surface maps to exit 3); the
        capability returns the status, the caller maps it to an exit code.
        """
        ...

    @abstractmethod
    def trash(self, grok_home: str, run_name: str, paths: Sequence[str]) -> tuple[str, ...]:
        """Move the validated paths into ``learn/trash/<run_name>``.

        Only a ``skills/<name>`` directory, a ``workflows/*.rhai`` file, or a
        ``hooks/*`` file under ``GROK_HOME`` / ``~/.agents`` / a project
        ``.grok`` directory is moved; anything else is refused.
        """
        ...

    @abstractmethod
    def decide(
        self,
        grok_home: str,
        run_dir: str,
        decision: TraceDecision,
    ) -> TraceDecision:
        """Append one decision line to ``learn/decisions.jsonl`` and return it."""
        ...

    @abstractmethod
    def wait(
        self, grok_home: str, run_dir: str, timeout_min: int = 90
    ) -> TraceStateStatus:
        """Block until the run dir holds ``report.md`` + ``actions.json``.

        Returns ``report_ready`` on success; the surface maps a deadline
        overrun to the legacy exit code.
        """
        ...

    def dispatch(
        self,
        grok_home: str,
        run_dir: str,
        action: str,
        flags: Mapping[str, str],
    ) -> TraceStateDispatchResult:
        """Route one trace-state sub-action through this capability.

        The thin router behind the agent's single per-op call; ``flags``
        carries the sub-action's parameters (status, run_name, paths, ...).
        """


__all__ = [
    "ISkillsCatalogProtocol",
    "ISkillsDiscovererProtocol",
    "ISkillsIndexProtocol",
    "ISkillsLintProtocol",
    "ISkillsMutatorProtocol",
    "ISkillsReaderProtocol",
    "ISkillsTracesProtocol",
    "ISkillsValidatorProtocol",
]