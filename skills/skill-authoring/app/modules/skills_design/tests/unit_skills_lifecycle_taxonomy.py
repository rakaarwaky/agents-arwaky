"""Unit tests for the skill lifecycle taxonomy.

Covers the lifecycle ``SkillsOp`` values, the ``ISkillsLifecycleProtocol``
seam, the named lifecycle VOs (``TelemetryRow``, ``LedgerEntry``,
``LIFECYCLE_STATES``), and the ``LifecycleConfig`` loader: defaults,
overlay parsing, and the missing/invalid-file fallback.
"""

from __future__ import annotations

import json
from abc import ABC
from pathlib import Path

import pytest
from shared.src.skills_design.contract_skills_protocol import (
    ISkillsLifecycleProtocol,
)
from shared.src.skills_design.taxonomy_skills_lifecycle_config_vo import (
    CONFIG_FILENAME,
    LifecycleConfig,
    load_lifecycle_config,
)
from shared.src.skills_design.taxonomy_skills_lifecycle_vo import (
    LIFECYCLE_STATES,
    LedgerEntry,
    TelemetryRow,
)
from shared.src.skills_design.taxonomy_skills_request import (
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)

_EXPECTED_LIFECYCLE_OPS = [
    "STATUS",
    "USAGE",
    "RUN",
    "PAUSE",
    "RESUME",
    "PIN",
    "UNPIN",
    "LOCK",
    "UNLOCK",
    "RESTORE",
    "PRUNE",
    "PURGE",
    "ADOPT",
    "BACKUP",
    "ROLLBACK",
    "LEDGER",
    "LIST_UNMANAGED",
    "LIST_ARCHIVED",
]

_EXPECTED_LIFECYCLE_VALUES = {
    "STATUS": "status",
    "USAGE": "usage",
    "RUN": "run",
    "PAUSE": "pause",
    "RESUME": "resume",
    "PIN": "pin",
    "UNPIN": "unpin",
    "LOCK": "lock",
    "UNLOCK": "unlock",
    "RESTORE": "restore",
    "PRUNE": "prune",
    "PURGE": "purge",
    "ADOPT": "adopt",
    "BACKUP": "backup",
    "ROLLBACK": "rollback",
    "LEDGER": "ledger",
    "LIST_UNMANAGED": "list-unmanaged",
    "LIST_ARCHIVED": "list-archived",
}


def test_every_expected_lifecycle_op_is_defined() -> None:
    for name in _EXPECTED_LIFECYCLE_OPS:
        assert hasattr(SkillsOp, name), f"SkillsOp missing {name}"
        member = getattr(SkillsOp, name)
        assert isinstance(member, SkillsOp)
        assert member.value == _EXPECTED_LIFECYCLE_VALUES[name]


def test_skills_request_round_trips_lifecycle_ops() -> None:
    for name in _EXPECTED_LIFECYCLE_OPS:
        op = getattr(SkillsOp, name)
        req = SkillsRequest(op=op)
        assert req.op is op
        assert req.op.value == _EXPECTED_LIFECYCLE_VALUES[name]


def test_lifecycle_states_tuple() -> None:
    assert LIFECYCLE_STATES == ("active", "stale", "archived")


def test_telemetry_row_dataclass() -> None:
    row = TelemetryRow(
        name="alpha",
        state="active",
        pinned=False,
        created_by="system",
        created_at="2026-01-01T00:00:00Z",
        first_seen_at="2026-01-01T00:00:00Z",
        last_activity_at=None,
        archived_at=None,
        views=10,
        uses=3,
        activity_window_start=None,
    )
    assert row.name == "alpha"
    assert row.views == 10
    assert row.locked is False

    with pytest.raises(AttributeError):
        row.views = 11  # frozen


def test_ledger_entry_dataclass() -> None:
    entry = LedgerEntry(
        id="abc",
        ts="2026-01-01T00:00:00Z",
        actor="system",
        action="patch",
        skill="alpha",
    )
    assert entry.id == "abc"
    assert entry.before == ()
    assert entry.evidence == {}

    with pytest.raises(AttributeError):
        entry.id = "def"  # frozen


def test_skills_lifecycle_protocol_is_abc() -> None:
    assert isinstance(ISkillsLifecycleProtocol, type)
    assert ISkillsLifecycleProtocol.__name__ == "ISkillsLifecycleProtocol"
    assert issubclass(ISkillsLifecycleProtocol, ABC)

    with pytest.raises(TypeError):
        ISkillsLifecycleProtocol()


def test_skills_lifecycle_protocol_declares_methods() -> None:
    required = {
        "curated_report",
        "apply_automatic_transitions",
        "snapshot_rollback",
        "ledger_append",
        "ledger_read",
        "ledger_compact",
    }
    for name in required:
        assert hasattr(ISkillsLifecycleProtocol, name)


def test_lifecycle_config_defaults() -> None:
    cfg = LifecycleConfig()
    assert cfg.enabled is True
    assert cfg.interval_hours == 168
    assert cfg.min_idle_hours == 2
    assert cfg.stale_after_days == 14
    assert cfg.archive_after_days == 30
    assert cfg.consolidate is False
    assert cfg.backup_enabled is True
    assert cfg.backup_keep == 2
    assert cfg.archive_ttl_days == 0
    assert cfg.pause is False


def test_load_lifecycle_config_missing_file_returns_defaults(tmp_path: Path) -> None:
    cfg = load_lifecycle_config(SkillsRoot(tmp_path))
    assert cfg == LifecycleConfig()


def test_load_lifecycle_config_overlays_values(tmp_path: Path) -> None:
    payload = {
        "stale_after_days": 7,
        "archive_after_days": 14,
        "backup": {"keep": 5, "enabled": False},
        "pause": True,
    }
    (tmp_path / CONFIG_FILENAME).write_text(json.dumps(payload), encoding="utf-8")
    cfg = load_lifecycle_config(SkillsRoot(tmp_path))
    assert cfg.stale_after_days == 7
    assert cfg.archive_after_days == 14
    assert cfg.backup_keep == 5
    assert cfg.backup_enabled is False
    assert cfg.pause is True
    assert cfg.enabled is True  # retained default
