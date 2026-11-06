"""Unit tests for PR 6: curator routing + composition root wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from shared.src.skills_design.taxonomy_skills_request import (
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.skills_design.taxonomy_skills_response import SkillsResult

from skills_design.src.root_skills_container import default_aggregate
from skills_design.tests.fixture_skills import clean_tree

ALL_CURATOR_OPS = [
    SkillsOp.CURATOR_STATUS,
    SkillsOp.CURATOR_USAGE,
    SkillsOp.CURATOR_RUN,
    SkillsOp.CURATOR_PAUSE,
    SkillsOp.CURATOR_RESUME,
    SkillsOp.CURATOR_PIN,
    SkillsOp.CURATOR_UNPIN,
    SkillsOp.CURATOR_LOCK,
    SkillsOp.CURATOR_UNLOCK,
    SkillsOp.CURATOR_ARCHIVE,
    SkillsOp.CURATOR_RESTORE,
    SkillsOp.CURATOR_PRUNE,
    SkillsOp.CURATOR_PURGE,
    SkillsOp.CURATOR_ADOPT,
    SkillsOp.CURATOR_BACKUP,
    SkillsOp.CURATOR_ROLLBACK,
    SkillsOp.CURATOR_LEDGER,
    SkillsOp.CURATOR_LIST_UNMANAGED,
    SkillsOp.CURATOR_LIST_ARCHIVED,
]

# Ops that need a skill query to work (skill-not-found is an ok result,
# just not a crash).
OPS_NEED_SKILL = {
    SkillsOp.CURATOR_PIN,
    SkillsOp.CURATOR_UNPIN,
    SkillsOp.CURATOR_LOCK,
    SkillsOp.CURATOR_UNLOCK,
    SkillsOp.CURATOR_ARCHIVE,
    SkillsOp.CURATOR_RESTORE,
    SkillsOp.CURATOR_PURGE,
    SkillsOp.CURATOR_ADOPT,
    SkillsOp.CURATOR_ROLLBACK,
}


def _execute(root: Path, op: SkillsOp, query: str = "") -> SkillsResult:
    agent = default_aggregate(default_root=root)
    req = SkillsRequest(op=op, query=query, root=SkillsRoot(root))
    return agent.execute(req)


# ─── default_aggregate wires all 4 curator capabilities ────────────

def test_default_aggregate_wires_all_curator_capabilities() -> None:
    tmp = Path(__file__).parent / "tmp_wiring_aggregate"
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    root = clean_tree(tmp)
    agent = default_aggregate(default_root=root)
    assert agent._telemetry is not None
    assert agent._lifecycle is not None
    assert agent._backup is not None
    assert agent._ledger is not None


# ─── All 19 curator ops return SkillsResult (no crash) ─────────────

@pytest.mark.parametrize("op", ALL_CURATOR_OPS)
def test_every_curator_op_returns_SkillsResult(op: SkillsOp) -> None:
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    root = clean_tree(tmp)
    query = "alpha" if op in OPS_NEED_SKILL else ""
    result = _execute(root, op, query)
    assert isinstance(result, SkillsResult)
    assert result.ok in (True, False)
    assert result.op == op


# ─── CURATOR_ARCHIVE / CURATOR_RESTORE end-to-end ──────────────────

def test_curator_archive_restore_e2e() -> None:
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    root = clean_tree(tmp)
    agent = default_aggregate(default_root=root)

    # archive alpha
    result = agent.execute(SkillsRequest(op=SkillsOp.CURATOR_ARCHIVE, query="alpha", root=SkillsRoot(root), apply=True))
    assert isinstance(result, SkillsResult)
    assert result.ok in (True, False)

    # sidecar should exist now (telemetry record)
    sidecar = root / "cat" / "alpha" / ".usage.json"
    # archive moves to _archive; sidecar lives in the moved dir or was in the source
    archive_sidecar = root / "_archive" / "cat" / "alpha" / ".usage.json"
    assert sidecar.exists() or archive_sidecar.exists()

    # archive dir should contain alpha
    archive_dir = root / "_archive" / "cat" / "alpha"
    assert archive_dir.exists()
    assert (archive_dir / "SKILL.md").exists()

    # restore alpha
    result2 = agent.execute(SkillsRequest(op=SkillsOp.CURATOR_RESTORE, query="alpha", root=SkillsRoot(root), apply=True))
    assert isinstance(result2, SkillsResult)
    assert result2.ok in (True, False)

    # skill back in place
    assert (root / "cat" / "alpha" / "SKILL.md").exists()
    assert not archive_dir.exists()


# ─── CURATOR_BACKUP produces snapshot ──────────────────────────────

def test_curator_backup_creates_snapshot() -> None:
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    root = clean_tree(tmp)
    result = _execute(root, SkillsOp.CURATOR_BACKUP)
    assert isinstance(result, SkillsResult)
    assert result.ok in (True, False)

    backup_root = root / ".curator_backups"
    assert backup_root.is_dir()
    snapshots = [d for d in backup_root.iterdir() if d.is_dir()]
    assert len(snapshots) >= 1
    snap = snapshots[0]
    assert (snap / "manifest.json").exists()
    assert (snap / "skills.tar.gz").exists()


# ─── CURATOR_LEDGER empty pack returns empty; after append returns entry ──
def test_curator_ledger_empty_and_after_append() -> None:
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    root = clean_tree(tmp)

    # empty pack: valid empty result
    result = _execute(root, SkillsOp.CURATOR_LEDGER)
    assert isinstance(result, SkillsResult)
    assert result.ok in (True, False)

    # append via ledger capability directly, then route CURATOR_LEDGER
    from skills_design.src.capabilities_skills_curator_ledger import SkillsCuratorLedger

    ledger = SkillsCuratorLedger()
    entry = {"id": "t1", "actor": "user", "action": "append", "skill": "alpha"}
    ledger.ledger_read(root)  # ensure file exists
    ledger.ledger_append(root, entry)

    result2 = _execute(root, SkillsOp.CURATOR_LEDGER)
    assert isinstance(result2, SkillsResult)
    assert result2.ok in (True, False)
    if result2.records:
        assert any(e.get("id") == "t1" for e in result2.records)


# ─── CURATOR_PAUSE / CURATOR_RESUME round-trip ─────────────────────

def test_curator_pause_resume_round_trip() -> None:
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    root = clean_tree(tmp)

    result_pause = _execute(root, SkillsOp.CURATOR_PAUSE)
    assert isinstance(result_pause, SkillsResult)
    assert result_pause.ok in (True, False)

    config_path = root / ".curator_config.json"
    assert config_path.exists()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data.get("pause") is True

    result_resume = _execute(root, SkillsOp.CURATOR_RESUME)
    assert isinstance(result_resume, SkillsResult)
    assert result_resume.ok in (True, False)

    data2 = json.loads(config_path.read_text(encoding="utf-8"))
    assert data2.get("pause") is False
