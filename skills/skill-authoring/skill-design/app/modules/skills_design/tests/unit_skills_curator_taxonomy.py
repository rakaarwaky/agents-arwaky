"""Unit tests for the curator taxonomy additions (curator-parity PR 1).

Covers the 19 curator ``SkillsOp`` values, the
``ISkillsCuratorProtocol`` seam, and the ``CuratorConfig`` loader:
defaults, overlay parsing, and the missing/invalid-file fallback.
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
from shared.src.skills_design.taxonomy_skills_request import SkillsOp, SkillsRoot

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

def test_all_19_curator_ops_are_distinct_and_importable() -> None:
    values = [getattr(SkillsOp, name).value for name in _EXPECTED_CURATOR_OPS]
    assert values == list(_EXPECTED_CURATOR_VALUES.values())
    assert len(set(values)) == len(values) == 19

def test_the_8_design_side_ops_are_unchanged() -> None:
    for name, value in _EXPECTED_DESIGN_OPS.items():
        assert getattr(SkillsOp, name).value == value
    design = set(_EXPECTED_DESIGN_OPS)
    assert not design & set(_EXPECTED_CURATOR_OPS)

def test_curator_protocol_has_all_6_abstract_methods() -> None:
    assert ISkillsCuratorProtocol.__abstractmethods__ == frozenset(
        {
            "apply_automatic_transitions",
            "curated_report",
            "ledger_append",
            "ledger_compact",
            "ledger_read",
            "snapshot_rollback",
        },
    )

def test_curator_config_defaults_match_the_doc_table() -> None:
    cfg = CuratorConfig()
    assert cfg == CuratorConfig(
        enabled=True,
        interval_hours=168,
        min_idle_hours=2,
        stale_after_days=14,
        archive_after_days=30,
        consolidate=False,
        backup_enabled=True,
        backup_keep=2,
        archive_ttl_days=0,
    )
    assert isinstance(cfg, CuratorConfig) and hash(cfg) == hash(CuratorConfig())

def test_load_missing_file_returns_defaults(tmp_path: Path) -> None:
    assert load_curator_config(SkillsRoot(tmp_path)) == CuratorConfig()

def test_load_valid_json_overlays_values(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps(
            {
                "stale_after_days": 7,
                "backup": {"enabled": False, "keep": 5},
                "interval_hours": 24,
            },
        ),
        encoding="utf-8",
    )
    cfg = load_curator_config(SkillsRoot(tmp_path))
    assert cfg.stale_after_days == 7
    assert cfg.backup_enabled is False
    assert cfg.backup_keep == 5
    assert cfg.interval_hours == 24
    assert cfg.archive_after_days == 30  # untouched default

def test_load_invalid_json_returns_defaults(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text("{not json", encoding="utf-8")
    assert load_curator_config(SkillsRoot(tmp_path)) == CuratorConfig()

def test_load_wrong_types_returns_defaults_for_bad_keys(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(
        json.dumps({"stale_after_days": "fourteen", "enabled": "no"}),
        encoding="utf-8",
    )
    cfg = load_curator_config(SkillsRoot(tmp_path))
    assert cfg.stale_after_days == 14
    assert cfg.enabled is True

def test_load_non_dict_json_returns_defaults(tmp_path: Path) -> None:
    (tmp_path / CONFIG_FILENAME).write_text(json.dumps([1, 2]), encoding="utf-8")
    assert load_curator_config(SkillsRoot(tmp_path)) == CuratorConfig()

@pytest.mark.parametrize("name", _EXPECTED_CURATOR_OPS)
def test_each_curator_op_member(name: str) -> None:
    assert SkillsOp[name].value == _EXPECTED_CURATOR_VALUES[name]
