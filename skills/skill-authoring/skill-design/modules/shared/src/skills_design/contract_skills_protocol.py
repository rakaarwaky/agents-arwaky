"""Skills contract protocols (AES contract layer, ABC traits).

One seam per CLI command the skills feature exposes: list, read,
lint, catalog, discover, move, archive, create, and the
trace-learning lifecycle. Capabilities implement these; the
composition root injects them into the agent.

Capabilities never import one another: where one needs another's
data (the discoverer reads catalog rows), the dependency is
expressed as one of these protocols and wired by the root.

The 13-rule validator checks live inline in
``capabilities_skills_linter.SkillsLinter``; they are not exposed as a CLI
verb. The mutation primitives (plan_weed, plan_repair) live in
``utility_skills_mutation`` (shared kernel), so no mutation protocol is
needed here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from shared.src.skills_design.taxonomy_skills_authoring_vo import (
    CatalogCheckResult,
    CatalogReport,
    CatalogRow,
    DiscoveryResult,
    LintReport,
    MutationOutcome,
    MutationPlan,
    NewCategoryPlan,
    SkillCreatePlan,
)
from shared.src.skills_design.taxonomy_skills_request import (
    SkillQuery,
    SkillsRoot,
)
from shared.src.skills_design.taxonomy_skills_rule_vo import (
    CategoryName,
    SkillName,
)
from shared.src.skills_design.taxonomy_skills_vo import (
    SkillContent,
    SkillRecord,
    SkillsJsonPayload,
)


class ISkillsListerProtocol(ABC):
    """Read-only listing of the skill pack."""

    @abstractmethod
    def list_skills(self, root: SkillsRoot | None = None) -> Sequence[SkillRecord]:
        """Return one record per skill, sorted by name.

        ``root`` overrides the capability's construction-time pack root
        (explicit beats derived); ``None`` keeps it.
        """
        ...

    def list_skills_json(self, root: SkillsRoot | None = None) -> SkillsJsonPayload:
        """Return the global-skill JSON list as a pure-data dict.

        One entry per skill (``name``, ``source``, ``path``, ``loaded``);
        the source is the repo pack only.
        """


class ISkillsReaderProtocol(ABC):
    """Read-only content access to one skill's SKILL.md."""

    @abstractmethod
    def show_skill(
        self, query: SkillQuery, root: SkillsRoot | None = None
    ) -> SkillContent | None:
        """Return the raw SKILL.md content for *query*, or None if missing."""
        ...


class ISkillsLinterProtocol(ABC):
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

    @abstractmethod
    def read(self, root: SkillsRoot) -> SkillContent:
        """Return the raw tracked ``CATALOG.md`` text, or ``""`` if missing.

        A read-only view for the CLI ``catalog --read`` path; unlike
        ``load_rows`` this never parses, drift-checks, or raises — it
        just hands the bytes back (empty string when the file is absent,
        so the caller decides how to report it).
        """
        ...


class ISkillsDiscoverProtocol(ABC):
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


class ISkillsMoverProtocol(ABC):
    """Plan/apply a move of a skill to another category (dry-run by default)."""

    @abstractmethod
    def plan_move(
        self, skill: SkillName, target: CategoryName, root: SkillsRoot
    ) -> MutationPlan:
        """Resolve a move to another category (pure; no writes)."""
        ...

    @abstractmethod
    def apply_move(self, plan: MutationPlan) -> MutationOutcome:
        """Execute a move plan; re-checks containment first."""
        ...


class ISkillsArchiverProtocol(ABC):
    """Plan/apply an archive of a skill into ``_archive/`` (dry-run by default)."""

    @abstractmethod
    def plan_archive(self, skill: SkillName, root: SkillsRoot) -> MutationPlan:
        """Resolve an archive into ``_archive/`` (pure; no writes)."""
        ...

    @abstractmethod
    def apply_archive(self, plan: MutationPlan) -> MutationOutcome:
        """Execute an archive plan; re-checks containment first."""
        ...


class ISkillsCreatorProtocol(ABC):
    """Create skills and categories in the pack (dry-run by default)."""

    @abstractmethod
    def create_skill(
        self,
        skill: SkillName,
        category: str,
        description: str,
        when_to_use: str,
        argument_hint: str,
        body: str,
        root: SkillsRoot,
        apply: bool,
    ) -> SkillCreatePlan:
        """Plan (or apply) creating a new skill SKILL.md.

        When ``apply`` is False the returned plan is a preview.
        When True, the file is written.
        """
        ...

    @abstractmethod
    def create_category(
        self,
        name: CategoryName,
        description: str,
        root: SkillsRoot,
        force: bool,
        apply: bool,
    ) -> NewCategoryPlan:
        """Plan (or apply) creating a category folder + DESCRIPTION.md.

        When ``apply`` is False the returned plan is a preview.
        When True, the directory and description file are written.
        """
        ...


# ── Internal seams end ──


__all__ = [
    "ISkillsArchiverProtocol",
    "ISkillsCatalogProtocol",
    "ISkillsCreatorProtocol",
    "ISkillsDiscoverProtocol",
    "ISkillsLinterProtocol",
    "ISkillsListerProtocol",
    "ISkillsMoverProtocol",
    "ISkillsReaderProtocol",
]
