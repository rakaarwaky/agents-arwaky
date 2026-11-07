"""Unit tests for the curator taxonomy additions (curator-parity PR 1).

Covers the 19 curator ``SkillsOp`` values, the
``ISkillsCuratorProtocol`` seam, the named curator VOs
(``TelemetryRow``, ``LedgerEntry``, ``LIFECYCLE_STATES``), and the
``CuratorConfig`` loader: defaults, overlay parsing, and the
missing/invalid-file fallback.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from shared.src.skills_design.contract_skills_protocol import (
    ISkillsCuratorProtocol,
)
from shared.src.skills_design.taxonomy_skills_curator_config_vo import (
    CONFIG_FILENAME,
    CuratorConfig,
    load_curator_config,
)
from shared.src.skills_design.taxonomy_skills_curator_vo import (
    LIFECYCLE_STATES,
    LedgerEntry,
    TelemetryRow,
)
from shared.src.skills_design.taxonomy_skills_request import (
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)

_EXPECTED_CURATOR_OPS = [
    "CURATOR_STATUS",
    "CURATOR_USAGE",
    "CURATOR_RUN",
    "CURATOR_PAUSE",
    "CURATOR_RESUME",
    "CURATOR_PIN",
    "CURATOR_UNPIN",
    "CURATOR_LOCK",
    "CURATOR_UNLOCK",
    "CURATOR_ARCHIVE",
    "CURATOR_RESTORE",
    "CURATOR_PRUNE",
    "CURATOR_PURGE",
    "CURATOR_ADOPT",
    "CURATOR_BACKUP",
    "CURATOR_ROLLBACK",
    "CURATOR_LEDGER",
    "CURATOR_LIST_UNMANAGED",
    "CURATOR_LIST_ARCHIVED",
]

_EXPECTED_CURATOR_VALUES = {
    "CURATOR_STATUS": "curator-status",
    "CURATOR_USAGE": "curator-usage",
    "CURATOR_RUN": "curator-run",
    "CURATOR_PAUSE": "curator-pause",
    "CURATOR_RESUME": "curator-resume",
    "CURATOR_PIN": "curator-pin",
    "CURATOR_UNPIN": "curator-unpin",
    "CURATOR_LOCK": "curator-lock",
    "CURATOR_UNLOCK": "curator-unlock",
    "CURATOR_ARCHIVE": "curator-archive",
    "CURATOR_RESTORE": "curator-restore",
    "CURATOR_PRUNE": "curator-prune",
    "CURATOR_PURGE": "curator-purge",
    "CURATOR_ADOPT": "curator-adopt",
    "CURATOR_BACKUP": "curator-backup",
    "CURATOR_ROLLBACK": "curator-rollback",
    "CURATOR_LEDGER": "curator-ledger",
    "CURATOR_LIST_UNMANAGED": "curator-list-unmanaged",
    "CURATOR_LIST_ARCHIVED": "curator-list-archived",
}

_EXPECTED_DESIGN_OPS = {
    "LIST": "list",
    "READ": "read",
    "LINT": "lint",
    "CATALOG": "catalog",
    "DISCOVER": "discover",
    "MOVE": "move",
    "ARCHIVE": "archive",
    "CREATE": "create",
}

_CURATOR_OPS = {
    op: getattr(SkillsOp, op) for op in _EXPECTED_CURATOR_OPS
}

_DESIGN_OPS = {
    op: getattr(SkillsOp, op) for op in _EXPECTED_DESIGN_OPS
}

_TEST_CURATOR_STATE_PATH = "/tmp/test-curator-state"


def test_skill_ops_adds_19_curator_ops() -> None:
    assert {op.value for op in _CURATOR_OPS.values()} == set(
        _EXPECTED_CURATOR_VALUES.values()
    )
    assert len(_EXPECTED_CURATOR_OPS) == 19

    for name, member in _CURATOR_OPS.items():
        assert member.value == _EXPECTED_CURATOR_VALUES[name]

    assert not set(_CURATOR_OPS) & set(_DESIGN_OPS)
    assert {op.value for op in _DESIGN_OPS.values()} == set(
        _EXPECTED_DESIGN_OPS.values()
    )


def test_skill_ops_total_is_27() -> None:
    assert len(list(SkillsOp)) == 27
    for member in SkillsOp:
        assert isinstance(member, str)
        assert isinstance(member, SkillsOp)
        assert isinstance(member.value, str)


def test_curator_ops_are_str_enum() -> None:
    for member in _CURATOR_OPS.values():
        assert isinstance(member, str)
        assert isinstance(member, SkillsOp)
        assert isinstance(member.value, str)


def test_design_ops_unchanged() -> None:
    assert {op.value for op in _DESIGN_OPS.values()} == set(
        _EXPECTED_DESIGN_OPS.values()
    )
    assert len(_EXPECTED_DESIGN_OPS) == 8


def test_design_ops_kept_their_original_values() -> None:
    assert _DESIGN_OPS["LIST"].value == "list"
    assert _DESIGN_OPS["READ"].value == "read"
    assert _DESIGN_OPS["LINT"].value == "lint"
    assert _DESIGN_OPS["CATALOG"].value == "catalog"
    assert _DESIGN_OPS["DISCOVER"].value == "discover"
    assert _DESIGN_OPS["MOVE"].value == "move"
    assert _DESIGN_OPS["ARCHIVE"].value == "archive"
    assert _DESIGN_OPS["CREATE"].value == "create"


def test_skills_request_is_unchanged() -> None:
    request = SkillsRequest(SkillsOp.LIST)
    assert request.op is SkillsOp.LIST
    assert request.query == ""
    assert request.root is None
    assert request.apply is False
    assert request.json is False
    assert request.description == ""
    assert request.flags == {}


def test_skill_s_request_is_unchanged() -> None:
    root = Path(_TEST_CURATOR_STATE_PATH)
    request = SkillsRequest(SkillsOp.MOVE, root=root)
    assert request.op is SkillsOp.MOVE
    assert request.root is root
    assert request.apply is False


def test_is_skills_curator_protocol_is_defined() -> None:
    assert isinstance(ISkillsCuratorProtocol, type)
    assert ISkillsCuratorProtocol.__name__ == "ISkillsCuratorProtocol"


def test_is_skills_curator_protocol_is_abstract() -> None:
    from abc import ABC

    assert issubclass(ISkillsCuratorProtocol, ABC)
    with pytest.raises(TypeError):
        ISkillsCuratorProtocol()


def test_is_skills_curator_protocol_has_required_methods() -> None:
    required = {
        "curated_report",
        "apply_automatic_transitions",
        "snapshot_rollback",
        "ledger_append",
        "ledger_read",
        "ledger_compact",
    }
    for name in required:
        method = getattr(ISkillsCuratorProtocol, name)
        assert callable(method)
        assert getattr(method, "__isabstractmethod__", False), name


def test_is_skills_curator_protocol_concrete_subclass_works() -> None:
    class _Stub(ISkillsCuratorProtocol):
        def curated_report(self, root: SkillsRoot) -> object:
            return ()

        def apply_automatic_transitions(self, root: SkillsRoot) -> dict:
            return {}

        def snapshot_rollback(
            self,
            root: SkillsRoot,
            action: str,
            id_: str | None = None,
        ) -> dict:
            return {}

        def ledger_append(self, root: SkillsRoot, entry: dict) -> dict:
            return entry

        def ledger_read(self, root: SkillsRoot) -> tuple[dict, ...]:
            return ()

        def ledger_compact(self, root: SkillsRoot) -> dict:
            return {}

    root = Path(_TEST_CURATOR_STATE_PATH)
    stub = _Stub()
    assert stub.curated_report(root) == ()
    assert stub.apply_automatic_transitions(root) == {}
    assert stub.snapshot_rollback(root, "backup") == {}
    assert stub.ledger_append(root, {"id": "x"}) == {"id": "x"}
    assert stub.ledger_read(root) == ()
    assert stub.ledger_compact(root) == {}


def test_curator_config_defaults_match_the_design_table() -> None:
    defaults = load_curator_config()
    expected = CuratorConfig()
    assert defaults == expected
    assert defaults.enabled is True
    assert defaults.interval_hours == 168
    assert defaults.min_idle_hours == 2
    assert defaults.stale_after_days == 14
    assert defaults.archive_after_days == 30
    assert defaults.consolidate is False
    assert defaults.backup_enabled is True
    assert defaults.backup_keep == 2
    assert defaults.archive_ttl_days == 0


def test_load_curator_config_overlays_flat_and_nested_keys(
    tmp_path: Path,
) -> None:
    config = {
        "enabled": False,
        "interval_hours": 24,
        "min_idle_hours": 10,
        "stale_after_days": 30,
        "archive_after_days": 60,
        "consolidate": True,
        "archive_ttl_days": 90,
        "backup": {"enabled": False, "keep": 5},
    }
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps(config),
        encoding="utf-8",
    )
    loaded = load_curator_config(tmp_path)
    assert loaded.enabled is False
    assert loaded.interval_hours == 24
    assert loaded.min_idle_hours == 10
    assert loaded.stale_after_days == 30
    assert loaded.archive_after_days == 60
    assert loaded.consolidate is True
    assert loaded.archive_ttl_days == 90
    assert loaded.backup_enabled is False
    assert loaded.backup_keep == 5


def test_load_curator_config_ignores_flat_backup_key(
    tmp_path: Path,
) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"backup": "soon", "backup_keep": 99}),
        encoding="utf-8",
    )
    loaded = load_curator_config(tmp_path)
    assert loaded.backup_enabled is True
    assert loaded.backup_keep == 99


def test_load_curator_config_wrong_types_fall_back_to_defaults(
    tmp_path: Path,
) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"enabled": "yes", "min_idle_hours": "soon"}),
        encoding="utf-8",
    )
    loaded = load_curator_config(tmp_path)
    assert loaded == CuratorConfig()


def test_load_curator_config_rejects_bool_for_int_keys(
    tmp_path: Path,
) -> None:
    # bool subclasses int; a JSON true for an int key must fall back.
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"interval_hours": True, "backup": {"keep": True}}),
        encoding="utf-8",
    )
    loaded = load_curator_config(tmp_path)
    assert loaded.interval_hours == 168
    assert loaded.backup_keep == 2


def test_load_curator_config_rejects_int_for_bool_keys(
    tmp_path: Path,
) -> None:
    # JSON 1/0 are ints, not bool; a bool key must reject them.
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"enabled": 1, "backup": {"enabled": 0}}),
        encoding="utf-8",
    )
    loaded = load_curator_config(tmp_path)
    assert loaded.enabled is True
    assert loaded.backup_enabled is True


def test_load_curator_config_missing_file_returns_defaults(
    tmp_path: Path,
) -> None:
    assert not (tmp_path / CONFIG_FILENAME).exists()
    assert load_curator_config(tmp_path) == CuratorConfig()


def test_load_curator_config_invalid_json_returns_defaults(
    tmp_path: Path,
) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        "{not json",
        encoding="utf-8",
    )
    assert load_curator_config(tmp_path) == CuratorConfig()


def test_load_curator_config_non_dict_returns_defaults(
    tmp_path: Path,
) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps(["enabled", "nope"]),
        encoding="utf-8",
    )
    assert load_curator_config(tmp_path) == CuratorConfig()


def test_curator_config_is_frozen() -> None:
    with pytest.raises(AttributeError):
        CuratorConfig().enabled = False  # type: ignore[misc]


def test_telemetry_row_fields_round_trip() -> None:
    row = TelemetryRow(
        name="alpha",
        state="active",
        pinned=True,
        created_by="human",
        created_at="2026-01-01T00:00:00Z",
        first_seen_at="2026-01-02T00:00:00Z",
        last_activity_at="2026-01-03T00:00:00Z",
        archived_at=None,
        views=10,
        uses=5,
        activity_window_start="2025-12-01T00:00:00Z",
    )
    assert row.name == "alpha"
    assert row.state == "active"
    assert row.pinned is True
    assert row.created_by == "human"
    assert row.created_at == "2026-01-01T00:00:00Z"
    assert row.first_seen_at == "2026-01-02T00:00:00Z"
    assert row.last_activity_at == "2026-01-03T00:00:00Z"
    assert row.archived_at is None
    assert row.views == 10
    assert row.uses == 5
    assert row.activity_window_start == "2025-12-01T00:00:00Z"


def test_telemetry_row_none_fields_round_trip() -> None:
    row = TelemetryRow(
        name="beta",
        state="stale",
        pinned=False,
        created_by=None,
        created_at=None,
        first_seen_at=None,
        last_activity_at=None,
        archived_at=None,
        views=0,
        uses=0,
        activity_window_start=None,
    )
    assert row.name == "beta"
    assert row.state == "stale"
    assert row.pinned is False
    assert row.created_by is None
    assert row.created_at is None
    assert row.first_seen_at is None
    assert row.last_activity_at is None
    assert row.archived_at is None
    assert row.views == 0
    assert row.uses == 0
    assert row.activity_window_start is None


def test_telemetry_row_is_frozen() -> None:
    row = TelemetryRow(
        name="alpha",
        state="active",
        pinned=True,
        created_by="human",
        created_at=None,
        first_seen_at=None,
        last_activity_at=None,
        archived_at=None,
        views=0,
        uses=0,
        activity_window_start=None,
    )
    with pytest.raises(AttributeError):
        row.name = "other"  # type: ignore[misc]


def test_ledger_entry_fields_round_trip() -> None:
    before = (
        {"path": "cat-a/good-skill/SKILL.md", "sha256": "aa"},
        {"path": "cat-a/good-skill/DESCRIPTION.md", "sha256": "bb"},
    )
    after = ({},)
    evidence = {"absorbed_into": "alpha"}
    entry = LedgerEntry(
        id="e-1",
        ts="2026-01-01T00:00:00Z",
        actor="hermes-curator",
        action="archive",
        skill="cat-a/good-skill",
        before=before,
        after=after,
        evidence=evidence,
    )
    assert entry.id == "e-1"
    assert entry.ts == "2026-01-01T00:00:00Z"
    assert entry.actor == "hermes-curator"
    assert entry.action == "archive"
    assert entry.skill == "cat-a/good-skill"
    assert entry.before == before
    assert entry.after == after
    assert entry.evidence == evidence


def test_ledger_entry_defaults_round_trip() -> None:
    entry = LedgerEntry(
        id="e-2",
        ts="2026-01-02T00:00:00Z",
        actor="hermes-curator",
        action="prune",
        skill="cat-b/orphan",
    )
    assert entry.before == ()
    assert entry.after == ()
    assert entry.evidence == {}


def test_ledger_entry_is_frozen() -> None:
    entry = LedgerEntry(
        id="e-3",
        ts="2026-01-03T00:00:00Z",
        actor="hermes-curator",
        action="restore",
        skill="cat-a/good-skill",
    )
    with pytest.raises(AttributeError):
        entry.id = "other"  # type: ignore[misc]


def test_lifecycle_states_tuple() -> None:
    assert LIFECYCLE_STATES == ("active", "stale", "archived")
    assert len(LIFECYCLE_STATES) == 3


def test_unwired_curator_op_dispatch_path() -> None:
    """A curator op with no capability wired must fail closed on bad root.

    PR 6: curator ops now route to handlers; the only failure path here is
    the missing skills root (which the handler reports as a SkillsResult,
    not an unhandled exception).
    """
    from skills_design.src.agent_skills_orchestrator import SkillsAgent

    agent = SkillsAgent(
        None,  # lister unused
        None,  # reader unused
    )
    request = SkillsRequest(SkillsOp.CURATOR_STATUS, root=Path("/nonexistent"))
    result = agent.execute(request)
    assert result.ok is False
    assert (
        "Skills telemetry capability is not configured" in result.message
        or "Skills root does not exist" in result.message
    )
