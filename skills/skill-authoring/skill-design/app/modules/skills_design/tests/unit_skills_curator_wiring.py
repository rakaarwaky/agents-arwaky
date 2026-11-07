"""Unit tests for PR 6: curator routing + composition root wiring."""

from __future__ import annotations

import json
from pathlib import Path

from shared.src.skills_design.taxonomy_skills_request import (
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.skills_design.taxonomy_skills_response import (
    SkillsExitCode,
    SkillsResult,
)

from skills_design.src.agent_skills_orchestrator import SkillsAgent
from skills_design.src.capabilities_skills_curator_backup import SkillsCuratorBackup
from skills_design.src.capabilities_skills_curator_ledger import SkillsCuratorLedger
from skills_design.src.capabilities_skills_curator_lifecycle import (
    SkillsCuratorLifecycle,
)
from skills_design.src.capabilities_skills_curator_telemetry import (
    SkillsCuratorTelemetry,
)
from skills_design.src.capabilities_skills_lister import SkillsLister
from skills_design.src.capabilities_skills_reader import SkillsPackReader
from skills_design.src.root_skills_container import default_aggregate
from skills_design.tests.fixture_skills import clean_tree


def _setup_pack_with_skill(tmp_path: Path, skill_name: str = "alpha") -> Path:
    root = clean_tree(tmp_path)
    skill_dir = root / "cat" / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    return root


def _execute(
    root: Path, op: SkillsOp, query: str = "", flags: dict | None = None
) -> SkillsResult:
    agent = default_aggregate(default_root=root)
    req = SkillsRequest(
        op=op, query=query, root=SkillsRoot(root), flags=flags or {}
    )
    return agent.execute(req)


# ─── default_aggregate wires all 4 curator capabilities ────────────

def test_default_aggregate_wires_all_curator_capabilities(tmp_path: Path) -> None:
    root = clean_tree(tmp_path)
    agent = default_aggregate(default_root=root)
    assert isinstance(agent, SkillsAgent)
    assert isinstance(agent._telemetry, SkillsCuratorTelemetry)
    assert isinstance(agent._lifecycle, SkillsCuratorLifecycle)
    assert isinstance(agent._backup, SkillsCuratorBackup)
    assert isinstance(agent._ledger, SkillsCuratorLedger)


# ─── Negative tests: unwired capabilities and missing query ──────────

def test_unwired_curator_capabilities_fail() -> None:
    agent = SkillsAgent(lister=SkillsLister(), reader=SkillsPackReader())
    req = SkillsRequest(op=SkillsOp.CURATOR_STATUS, root=SkillsRoot("."))
    result = agent.execute(req)
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.USAGE_ERROR


def test_curator_pin_missing_query_fails(tmp_path: Path) -> None:
    root = clean_tree(tmp_path)
    result = _execute(root, SkillsOp.CURATOR_PIN, query="")
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.ISSUES_FOUND
    assert "Skill name required" in result.message


def test_curator_pin_unknown_skill_fails(tmp_path: Path) -> None:
    root = clean_tree(tmp_path)
    result = _execute(root, SkillsOp.CURATOR_PIN, query="unknown_skill")
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.ISSUES_FOUND
    assert "Skill not found" in result.message


# ─── Functional test: PIN / UNPIN / LOCK / UNLOCK ────────────────────

def test_curator_pin_unpin_mutates_sidecar(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    sidecar = root / "cat" / "alpha" / ".usage.json"

    res_pin = _execute(root, SkillsOp.CURATOR_PIN, query="alpha")
    assert res_pin.ok is True
    assert res_pin.exit_code == SkillsExitCode.CLEAN
    assert json.loads(sidecar.read_text(encoding="utf-8"))["pinned"] is True

    res_unpin = _execute(root, SkillsOp.CURATOR_UNPIN, query="alpha")
    assert res_unpin.ok is True
    assert res_unpin.exit_code == SkillsExitCode.CLEAN
    assert json.loads(sidecar.read_text(encoding="utf-8"))["pinned"] is False


def test_curator_lock_unlock_mutates_sidecar(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    sidecar = root / "cat" / "alpha" / ".usage.json"

    res_lock = _execute(root, SkillsOp.CURATOR_LOCK, query="alpha")
    assert res_lock.ok is True
    assert res_lock.exit_code == SkillsExitCode.CLEAN
    assert json.loads(sidecar.read_text(encoding="utf-8"))["locked"] is True

    res_unlock = _execute(root, SkillsOp.CURATOR_UNLOCK, query="alpha")
    assert res_unlock.ok is True
    assert res_unlock.exit_code == SkillsExitCode.CLEAN
    assert json.loads(sidecar.read_text(encoding="utf-8"))["locked"] is False


# ─── Functional test: ADOPT ──────────────────────────────────────────

def test_curator_adopt_marks_agent_managed(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    sidecar = root / "cat" / "alpha" / ".usage.json"
    sidecar.write_text(json.dumps({"created_by": "user"}), encoding="utf-8")

    result = _execute(root, SkillsOp.CURATOR_ADOPT, query="alpha")
    assert result.ok is True
    assert result.exit_code == SkillsExitCode.CLEAN
    assert json.loads(sidecar.read_text(encoding="utf-8"))["created_by"] == "agent"


# ─── Functional test: LIST_UNMANAGED and LIST_ARCHIVED ───────────────

def test_curator_list_unmanaged_does_not_mutate_disk(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "beta")
    sidecar = root / "cat" / "beta" / ".usage.json"
    assert not sidecar.exists()

    result = _execute(root, SkillsOp.CURATOR_LIST_UNMANAGED)
    assert result.ok is True
    assert result.exit_code == SkillsExitCode.CLEAN
    assert any(r.get("name") == "beta" for r in result.records)
    # Crucial: list-unmanaged must not seed .usage.json on disk!
    assert not sidecar.exists()


def test_curator_list_archived_finds_archived_skills(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "gamma")
    _execute(root, SkillsOp.CURATOR_ARCHIVE, query="gamma")

    result = _execute(root, SkillsOp.CURATOR_LIST_ARCHIVED)
    assert result.ok is True
    assert result.exit_code == SkillsExitCode.CLEAN
    assert any(r.get("name") == "gamma" for r in result.records)


# ─── CURATOR_ARCHIVE + CURATOR_RESTORE round-trip ────────────────────

def test_curator_archive_restore_round_trip(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    archive_dir = root / "_archive" / "cat" / "alpha"

    res_archive = _execute(root, SkillsOp.CURATOR_ARCHIVE, query="alpha")
    assert res_archive.ok is True
    assert res_archive.exit_code == SkillsExitCode.CLEAN
    assert archive_dir.is_dir()
    assert not (root / "cat" / "alpha").exists()

    res_restore = _execute(root, SkillsOp.CURATOR_RESTORE, query="alpha")
    assert res_restore.ok is True
    assert res_restore.exit_code == SkillsExitCode.CLEAN
    assert (root / "cat" / "alpha" / "SKILL.md").exists()
    assert not archive_dir.exists()


# ─── CURATOR_BACKUP produces snapshot ──────────────────────────────

def test_curator_backup_creates_snapshot(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    result = _execute(root, SkillsOp.CURATOR_BACKUP)
    assert result.ok is True
    assert result.exit_code == SkillsExitCode.CLEAN

    backup_root = root / ".curator_backups"
    assert backup_root.is_dir()
    snapshots = [d for d in backup_root.iterdir() if d.is_dir() and d.name != "blobs"]
    assert len(snapshots) >= 1
    snap = snapshots[0]
    assert (snap / "manifest.json").exists()
    assert (snap / "skills.tar.gz").exists()


# ─── CURATOR_LEDGER ─────────────────────────────────────────────────

def test_curator_ledger_empty_and_after_append(tmp_path: Path) -> None:
    root = clean_tree(tmp_path)

    result = _execute(root, SkillsOp.CURATOR_LEDGER)
    assert result.ok is True
    assert result.exit_code == SkillsExitCode.CLEAN
    assert result.records == ()

    ledger = SkillsCuratorLedger()
    entry = {"id": "t1", "actor": "user", "action": "append", "skill": "alpha"}
    ledger.ledger_read(root)
    ledger.ledger_append(root, entry)

    result2 = _execute(root, SkillsOp.CURATOR_LEDGER)
    assert result2.ok is True
    assert result2.exit_code == SkillsExitCode.CLEAN
    assert any(e.get("id") == "t1" for e in result2.records)


# ─── CURATOR_PAUSE / CURATOR_RESUME round-trip ─────────────────────

def test_curator_pause_resume_round_trip(tmp_path: Path) -> None:
    root = clean_tree(tmp_path)

    result_pause = _execute(root, SkillsOp.CURATOR_PAUSE)
    assert result_pause.ok is True
    assert result_pause.exit_code == SkillsExitCode.CLEAN

    config_path = root / ".curator_config.json"
    assert config_path.exists()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert data.get("pause") is True

    result_resume = _execute(root, SkillsOp.CURATOR_RESUME)
    assert result_resume.ok is True
    assert result_resume.exit_code == SkillsExitCode.CLEAN

    data2 = json.loads(config_path.read_text(encoding="utf-8"))
    assert data2.get("pause") is False


# ─── CURATOR_STATUS / USAGE / RUN / PRUNE / PURGE ───────────────────

def test_curator_status_and_usage(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    res_status = _execute(root, SkillsOp.CURATOR_STATUS)
    assert res_status.ok is True
    assert res_status.exit_code == SkillsExitCode.CLEAN

    res_usage = _execute(root, SkillsOp.CURATOR_USAGE)
    assert res_usage.ok is True
    assert res_usage.exit_code == SkillsExitCode.CLEAN


def test_curator_run(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    result = _execute(root, SkillsOp.CURATOR_RUN)
    assert result.ok is True
    assert result.exit_code == SkillsExitCode.CLEAN


def test_curator_prune_and_purge(tmp_path: Path) -> None:
    root = _setup_pack_with_skill(tmp_path, "alpha")
    res_prune = _execute(root, SkillsOp.CURATOR_PRUNE, flags={"days": 30})
    assert res_prune.ok is True
    assert res_prune.exit_code == SkillsExitCode.CLEAN

    # archive alpha first then purge
    _execute(root, SkillsOp.CURATOR_ARCHIVE, query="alpha")
    res_purge = _execute(root, SkillsOp.CURATOR_PURGE, query="alpha")
    assert res_purge.ok is True
    assert res_purge.exit_code == SkillsExitCode.CLEAN
