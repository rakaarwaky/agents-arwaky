"""Curator contract value objects (AES taxonomy layer, curator side).

Named VOs backing the ``ISkillsCuratorProtocol`` seam (curator-parity
redesign PR 1): telemetry rows, the automatic-transition summary,
snapshot/rollback results, and audit-ledger entries. Fields mirror the
design doc's data model (``skill-telemetry.md``, ``curator-lifecycle.md``,
``curator-snapshot-rollback.md``, ``skill-audit-ledger.md``).

Pure data; no I/O, no imports from utility/capabilities/agent/root/
surface layers. The contract module imports these under ``TYPE_CHECKING``
only, so a runtime import back into the contract would be the only cycle
these types can introduce, and they need no runtime imports of their own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "CuratorTransitionReport",
    "CuratorTransitionSummary",
    "CuratorUsageRow",
    "LedgerCompactSummary",
    "LedgerEntry",
    "SnapshotRollbackResult",
    "TelemetryRow",
]

#: Lifecycle states a curator-managed skill can hold.
LIFECYCLE_STATES = ("active", "stale", "archived")

@dataclass(frozen=True)
class TelemetryRow:
    """One row of ``curated_report``: the auto-transition source of truth.

    Mirrors the ``.usage.json`` per-skill record (``skill-telemetry.md``);
    timestamps are ISO strings, or ``None`` when never set.
    """

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

@dataclass(frozen=True)
class CuratorUsageRow:
    """One row of the ``curator usage`` view (telemetry + provenance)."""

    name: str
    state: str
    uses: int
    views: int
    last_activity_at: str | None
    pinned: bool

@dataclass(frozen=True)
class CuratorTransitionReport:
    """One automatic transition the pass applied (or would, in dry-run)."""

    skill: str
    from_state: str
    to_state: str
    reason: str

@dataclass(frozen=True)
class CuratorTransitionSummary:
    """Result of one ``apply_automatic_transitions`` pass."""

    applied: tuple[CuratorTransitionReport, ...] = ()
    skipped: dict[str, int] = field(default_factory=dict)

    @property
    def count(self) -> int:
        """How many transitions the pass applied."""
        return len(self.applied)

@dataclass(frozen=True)
class SnapshotRollbackResult:
    """Outcome of a snapshot or rollback operation.

    ``id_`` is the UTC-ISO snapshot id a ``backup`` created or a
    ``rollback`` restored; empty for failures, which then carry
    ``error``.
    """

    id_: str = ""
    error: str | None = None
    restored_files: int = 0

@dataclass(frozen=True)
class LedgerEntry:
    """One append-only audit-ledger row (``skill-audit-ledger.md``).

    Manifests are lists of ``{"path": ..., "sha256": ...}`` dicts; blobs
    live under ``.curator_backups/blobs/``. ``evidence`` is freeform
    (``absorbed_into``, ``rollback_target``, ...).
    """

    id: str
    ts: str
    actor: str
    action: str
    skill: str
    before: tuple[dict[str, Any], ...] = ()
    after: tuple[dict[str, Any], ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class LedgerCompactSummary:
    """Result of one ledger/blob compaction pass."""

    blobs_removed: int = 0
    entries_kept: int = 0
    bytes_freed: int = 0
