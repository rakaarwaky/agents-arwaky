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
from pathlib import Path

from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsRoot,
)
from shared.src.common.taxonomy_common_vo import (
    BM25FHit,
    CatalogCheckResult,
    CatalogReport,
    CategoryName,
    DiscoveryResult,
    SkillContent,
    SkillName,
    SkillRecord,
    SkillsJsonPayload,
)
from shared.src.design.taxonomy_skills_vo import (
    LintReport,
    MutationOutcome,
    MutationPlan,
    NewCategoryPlan,
    SkillCreatePlan,
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
    """Render, rebuild, check, and read the tracked ``catalog.json``."""

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
    def read(self, root: SkillsRoot) -> SkillContent:
        """Return the raw tracked ``catalog.json`` text, or ``""`` if missing.

        A read-only view for the CLI ``catalog --read`` path; never parses,
        drift-checks, or raises — it just hands the bytes back (empty
        string when the file is absent, so the caller decides how to report
        it).
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
        search tokens (exit 2). On drift (a missing or corrupt
        ``catalog.json``), sets the result's warning fields, falls back to the
        live tree scan, and returns matches with exit 0.
        """
        ...

    @abstractmethod
    def rank(self, rows: object, tokens: list[str]) -> list[BM25FHit]:
        """Return ranked hits for *rows* scored against *tokens*.

        Each hit carries a float ``score``, the original row, and the
        logical field names that contributed (``matched_fields``).
        Empty *rows* or *tokens* yield an empty list.
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


# ── Internal seams end ──


class ISkillsPinerProtocol(ABC):
    """Piner capability: pin/unpin verbs."""

    @abstractmethod
    def pin(self, skill: str, root: SkillsRoot | None = None) -> dict:
        ...

    @abstractmethod
    def unpin(self, skill: str, root: SkillsRoot | None = None) -> dict:
        ...

class ISkillsLockerProtocol(ABC):
    """Locker capability: lock/unlock verbs."""

    @abstractmethod
    def lock(self, skill: str, root: SkillsRoot | None = None) -> dict:
        ...

    @abstractmethod
    def unlock(self, skill: str, root: SkillsRoot | None = None) -> dict:
        ...

class ISkillsRestoreProtocol(ABC):
    """Restore capability: archive / restore verbs."""

    @abstractmethod
    def archive(self, skill: str, root: SkillsRoot | None = None) -> dict:
        ...

    @abstractmethod
    def restore(self, skill: str, root: SkillsRoot | None = None) -> dict:
        ...

class ISkillsPruneProtocol(ABC):
    """Prune capability: bulk-archive idle skills."""

    @abstractmethod
    def prune(
        self,
        root: SkillsRoot | None = None,
        days: int | None = None,
        dry_run: bool = False,
    ) -> dict:
        ...

class ISkillsPurgeProtocol(ABC):
    """Purge capability: delete archived skills."""

    @abstractmethod
    def purge(
        self,
        skill: str | None = None,
        root: SkillsRoot | None = None,
        dry_run: bool = False,
    ) -> dict:
        ...

class ISkillsAdopterProtocol(ABC):
    """Adopter capability: adopt verb."""

    @abstractmethod
    def adopt(self, skill: str, root: SkillsRoot | None = None) -> dict:
        ...

class ISkillsBackupProtocol(ABC):
    """Backup capability: snapshot create / prune."""

    @abstractmethod
    def create_snapshot(self, root: Path, *, _prune: bool = True) -> Path:
        ...

    @abstractmethod
    def prune_old_snapshots(
        self, root: Path, *, excluded: frozenset[str] | None = None
    ) -> list[Path]:
        ...

    @abstractmethod
    def resolve_root(self, root: Path) -> Path:
        """Validate and return the pack root, raising ``SkillsRootError``."""
        ...

    @abstractmethod
    def backup_root(self, skills_root: Path) -> Path:
        """Return (creating if needed) the snapshot directory under *skills_root*."""
        ...

class ISkillsRollbackProtocol(ABC):
    """Rollback capability: restore pack from snapshot."""

    @abstractmethod
    def rollback(self, root: SkillsRoot | Path, id_: str | None = None) -> dict:
        ...

class ISkillsLedgerProtocol(ABC):
    """Ledger capability: append / read / compact / rollback."""

    @abstractmethod
    def ledger_append(self, root: SkillsRoot | Path, entry: dict) -> dict:
        ...

    @abstractmethod
    def ledger_read(
        self,
        root: SkillsRoot | Path,
        limit: int | None = None,
    ) -> tuple[dict, ...]:
        ...

    @abstractmethod
    def ledger_compact(
        self,
        root: SkillsRoot | Path,
        older_than_days: int | None = None,
        keep_recent: int = 0,
    ) -> dict:
        ...

    @abstractmethod
    def rollback_entry(self, root: SkillsRoot | Path, entry_id: str) -> dict:
        ...

class ISkillsTelemetryProtocol(ABC):
    """Telemetry capability: usage tracking and status reports."""

    @abstractmethod
    def seed_record_if_missing(self, skill: str, root: SkillsRoot) -> None:
        ...

    @abstractmethod
    def reanchor_clock(self, skill: str, root: SkillsRoot) -> None:
        ...

    @abstractmethod
    def curated_report(self, root: SkillsRoot) -> list[dict]:
        ...

    @abstractmethod
    def view(self, skill: str, root: SkillsRoot) -> None:
        ...

class ISkillsRunnerProtocol(ABC):
    """Runner capability: run/pause/resume lifecycle verbs."""

    @abstractmethod
    def apply_automatic_transitions(self, root: SkillsRoot | None = None) -> dict:
        ...

    @abstractmethod
    def pause(self, root: SkillsRoot) -> dict:
        ...

    @abstractmethod
    def resume(self, root: SkillsRoot) -> dict:
        ...

__all__ = [
    "ISkillsAdopterProtocol",
    "ISkillsArchiverProtocol",
    "ISkillsBackupProtocol",
    "ISkillsCatalogProtocol",
    "ISkillsCreatorProtocol",
    "ISkillsDiscoverProtocol",
    "ISkillsLedgerProtocol",
    "ISkillsLinterProtocol",
    "ISkillsListerProtocol",
    "ISkillsLockerProtocol",
    "ISkillsMoverProtocol",
    "ISkillsPinerProtocol",
    "ISkillsPruneProtocol",
    "ISkillsPurgeProtocol",
    "ISkillsReaderProtocol",
    "ISkillsRestoreProtocol",
    "ISkillsRollbackProtocol",
    "ISkillsRunnerProtocol",
    "ISkillsTelemetryProtocol",
]
