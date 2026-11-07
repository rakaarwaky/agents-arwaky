"""Lifecycle value objects (AES taxonomy layer).

The named VOs for skill lifecycle management: the telemetry row and
the audit-ledger entry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "LIFECYCLE_STATES",
    "LedgerEntry",
    "TelemetryRow",
]

#: Lifecycle states a skill can hold.
LIFECYCLE_STATES = ("active", "stale", "archived")

@dataclass(frozen=True)
class TelemetryRow:
    """One telemetry row: the auto-transition source of truth."""

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
    """One append-only audit-ledger row."""

    id: str
    ts: str
    actor: str
    action: str
    skill: str
    before: tuple[dict[str, Any], ...] = ()
    after: tuple[dict[str, Any], ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)
