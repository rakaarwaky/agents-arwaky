"""Skills contract protocols (AES contract layer, ABC traits).

One seam per subsystem the skills agent coordinates: the pack index
(list), the pack reader (show), the validator, the catalog, discovery,
the mutator, the merge planner, and the rules renderer. Capabilities
implement these; the composition root injects them into the agent.

Capabilities never import one another: where one needs another's data
(the discoverer reads catalog rows), the dependency is expressed as one
of these protocols and wired by the root.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from modules.shared.src.skills.taxonomy_skills_authoring_vo import (
    CatalogCheckResult,
    CatalogReport,
    CatalogRow,
    DiscoveryResult,
    MergePlan,
    MutationOutcome,
    MutationPlan,
    NewCategoryPlan,
    RulesDocument,
    ValidationReport,
)
from modules.shared.src.skills.taxonomy_skills_rule_vo import (
    CategoryName,
    SkillName,
    SkillRef,
)
from modules.shared.src.skills.taxonomy_skills_vo import (
    RulesSummary,
    SkillContent,
    SkillDescription,
    SkillQuery,
    SkillRecord,
    SkillsRoot,
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


class ISkillsMergePlannerProtocol(ABC):
    """Read-only merge planning for ``skill-lifecycle``."""

    @abstractmethod
    def plan(self, ref_a: SkillRef, ref_b: SkillRef, root: SkillsRoot) -> MergePlan:
        """Build the plan for merging two ``category/skill`` references."""
        ...

    @abstractmethod
    def render(self, plan: MergePlan) -> tuple[str, ...]:
        """Render a plan as the markdown report ``skill-lifecycle`` consumes."""
        ...


class ISkillsRulesRendererProtocol(ABC):
    """Render the rule SSOT for humans and for the generated artifact."""

    @abstractmethod
    def render_markdown(self) -> RulesDocument:
        """Render the full rules document (the ``--markdown`` form)."""
        ...

    @abstractmethod
    def render_summary(self) -> RulesSummary:
        """Render the compact one-line-per-rule summary."""
        ...


__all__ = [
    "ISkillsCatalogProtocol",
    "ISkillsDiscovererProtocol",
    "ISkillsIndexProtocol",
    "ISkillsMergePlannerProtocol",
    "ISkillsMutatorProtocol",
    "ISkillsReaderProtocol",
    "ISkillsRulesRendererProtocol",
    "ISkillsValidatorProtocol",
]