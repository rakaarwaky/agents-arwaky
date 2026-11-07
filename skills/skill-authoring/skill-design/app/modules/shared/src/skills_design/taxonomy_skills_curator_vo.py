"""Curator contract value objects (AES taxonomy layer, curator side).

The two named VOs the design doc's data model prescribes for
curator-parity redesign PR 1: the ``curated_report`` telemetry row and
the audit-ledger entry. The ``ISkillsCuratorProtocol`` seam types its
remaining methods with raw ``dict`` / ``object`` per the doc, so no
other named types live here.

Pure data; no I/O, no imports from utility/capabilities/agent/root/
surface layers. The contract module imports these under ``TYPE_CHECKING``
only, so a runtime import back into the contract would be the only cycle
these types can introduce, and they need no runtime imports of their own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "LedgerEntry",
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
    locked: bool = False

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
