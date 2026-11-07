"""Unit tests for the focused lifecycle capabilities (sidecar + ``_archive/`` move)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from shared.src.skills_design.taxonomy_skills_error import (
    MutationConflictError,
    SkillNotFoundError,
)
from shared.src.skills_design.utility_lifecycle_support import _parse_iso

from skills_design.src.capabilities_skills_prune import SkillsPrune
from skills_design.src.capabilities_skills_purge import SkillsPurge
from skills_design.src.capabilities_skills_restore import SkillsRestore
from skills_design.src.capabilities_skills_runner import SkillsRunner
from skills_design.tests.fixture_skills import as_root

# ─── helpers ─────────────────────────────────────────────────────────


def _ago_iso(days: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


def _skill(
    root: Path,
    name: str,
    state: str = "active",
    pinned: bool = False,
    uses: int = 1,
    created_days: float | None = None,
    last_activity_days: float | None = None,
    window_days: float | None = None,
    locked: bool = False,
    archived_days: float | None = None,
) -> Path:
    """Create a skill dir under ``<root>/cat/`` with a populated sidecar."""
    cat = root / "cat"
    cat.mkdir(parents=True, exist_ok=True)
    skill_dir = cat / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: x\n---\n",
        encoding="utf-8",
    )
    record: dict = {
        "state": state,
        "pinned": pinned,
        "created_by": "agent",
        "created_at": _ago_iso(created_days if created_days is not None else 2),
        "first_seen_at": _ago_iso(2),
        "last_activity_at": _ago_iso(
            last_activity_days if last_activity_days is not None else 2
        ),
        "archived_at": _ago_iso(archived_days) if archived_days is not None else "",
        "views": 0,
        "uses": uses,
        "activity_window_start": _ago_iso(
            window_days if window_days is not None else 2
        ),
    }
    if locked:
        record["locked"] = True
    (skill_dir / ".usage.json").write_text(
        json.dumps(record, ensure_ascii=False),
        encoding="utf-8",
    )
    return skill_dir


def _read_sidecar(skill_dir: Path) -> dict:
    return json.loads((skill_dir / ".usage.json").read_text(encoding="utf-8"))


def _pack_empty(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    (root / "cat").mkdir(parents=True)
    return root


# ─── apply_automatic_transitions: empty pack ─────────────────────────

def test_empty_pack_yields_empty_summary(tmp_path: Path) -> None:
    """No skills, no sidecars: summary is empty and nothing was written."""
    root = _pack_empty(tmp_path)
    summary = SkillsRunner().apply_automatic_transitions(as_root(root))
    assert summary == {
        "applied": [],
        "skipped": [],
        "state_counts": {"active": 0, "stale": 0, "archived": 0},
    }
    assert not list(root.glob("**/.usage.json"))


# ─── apply_automatic_transitions: active → stale ────────────────────

def test_active_to_stale_updates_on_disk_sidecar(tmp_path: Path) -> None:
    """``last_activity_at`` 20 days ago (> 14) → state is stale on disk."""
    root = _pack_empty(tmp_path)
    _skill(root, "a20", state="active", last_activity_days=20)
    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    applied = [entry for entry in summary["applied"] if entry["skill"] == "a20"]
    assert len(applied) == 1
    assert applied[0]["from"] == "active"
    assert applied[0]["to"] == "stale"

    record = _read_sidecar(root / "cat" / "a20")
    assert record["state"] == "stale"
    assert summary["state_counts"]["stale"] == 1


def test_active_recent_skill_stays_active(tmp_path: Path) -> None:
    """``last_activity_at`` 2 days ago (< 14) → no transition applied."""
    root = _pack_empty(tmp_path)
    _skill(root, "fresh", state="active", last_activity_days=2)
    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    assert summary["applied"] == []
    assert _read_sidecar(root / "cat" / "fresh")["state"] == "active"
    assert summary["state_counts"]["active"] == 1


# ─── apply_automatic_transitions: stale → active reactivation ───────

def test_stale_to_active_reactivation_reanchors_clock(tmp_path: Path) -> None:
    """``activity_window_start`` within 14 days + old last_activity → active, reanchored."""
    root = _pack_empty(tmp_path)
    _skill(
        root,
        "react",
        state="stale",
        last_activity_days=40,
        window_days=5,
    )
    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    applied = [entry for entry in summary["applied"] if entry["skill"] == "react"]
    assert applied == [{"skill": "react", "from": "stale", "to": "active"}]

    record = _read_sidecar(root / "cat" / "react")
    assert record["state"] == "active"
    assert record["activity_window_start"] > _ago_iso(1)
    assert record["last_activity_at"] > _ago_iso(1)


# ─── apply_automatic_transitions: stale → archived ──────────────────

def test_stale_to_archived_sets_archived_at(tmp_path: Path) -> None:
    """``last_activity_at`` 35 days ago (> 30) → archived + ``archived_at`` set."""
    root = _pack_empty(tmp_path)
    _skill(
        root,
        "arch35",
        state="stale",
        last_activity_days=35,
        window_days=35,
    )
    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    applied = [entry for entry in summary["applied"] if entry["skill"] == "arch35"]
    assert applied == [{"skill": "arch35", "from": "stale", "to": "archived"}]

    record = _read_sidecar(root / "cat" / "arch35")
    assert record["state"] == "archived"
    assert record["archived_at"]
    assert summary["state_counts"]["archived"] == 1


# ─── apply_automatic_transitions: never-archive-young-unused invariant ──

def test_young_unused_skill_stays_active(tmp_path: Path) -> None:
    """``uses == 0`` + ``created_at`` 5 days ago (within 14) → active, even if last_activity is old."""
    root = _pack_empty(tmp_path)
    _skill(
        root,
        "young",
        state="active",
        uses=0,
        created_days=5,
        last_activity_days=20,
    )
    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    # Precondition: the last_activity anchor sits inside the stale-eligible
    # window, so the invariant (not any other condition) is what keeps the
    # record active.
    now = datetime.now(UTC)
    stale_cutoff = now - timedelta(days=14)
    last_activity = _parse_iso(_read_sidecar(root / "cat" / "young")["last_activity_at"])
    assert last_activity < stale_cutoff

    assert {"skill": "young", "reason": "young-unused"} in summary["skipped"]
    assert _read_sidecar(root / "cat" / "young")["state"] == "active"
    assert summary["state_counts"]["active"] == 1


def test_young_unused_stale_still_archives_after_archive_cutoff(tmp_path: Path) -> None:
    """``uses == 0`` + old ``created_at`` → invariant does not block archival."""
    root = _pack_empty(tmp_path)
    _skill(
        root,
        "old-unused",
        state="stale",
        uses=0,
        created_days=60,
        last_activity_days=35,
        window_days=35,
    )
    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    assert [entry for entry in summary["applied"] if entry["skill"] == "old-unused"] == [
        {"skill": "old-unused", "from": "stale", "to": "archived"},
    ]
    assert _read_sidecar(root / "cat" / "old-unused")["state"] == "archived"


# ─── apply_automatic_transitions: pinned / locked / cron skip ───────

def test_pinned_skill_is_unchanged(tmp_path: Path) -> None:
    """Pinned skill in a stale-eligible state: sidecar is byte-identical."""
    root = _pack_empty(tmp_path)
    skill_dir = _skill(root, "pin", state="active", pinned=True, last_activity_days=40)
    before = skill_dir.joinpath(".usage.json").read_bytes()

    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    assert {"skill": "pin", "reason": "pinned"} in summary["skipped"]
    assert skill_dir.joinpath(".usage.json").read_bytes() == before
    assert _read_sidecar(skill_dir)["state"] == "active"


def test_locked_skill_is_unchanged(tmp_path: Path) -> None:
    """Locked skill in a stale-eligible state: sidecar is byte-identical."""
    root = _pack_empty(tmp_path)
    skill_dir = _skill(
        root, "lock", state="active", locked=True, last_activity_days=40
    )
    before = skill_dir.joinpath(".usage.json").read_bytes()

    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    assert {"skill": "lock", "reason": "locked"} in summary["skipped"]
    assert skill_dir.joinpath(".usage.json").read_bytes() == before


def test_cron_referenced_skill_is_unchanged(tmp_path: Path) -> None:
    """Skill named in ``.cron/jobs.json``: sidecar is byte-identical."""
    root = _pack_empty(tmp_path)
    skill_dir = _skill(root, "cr", state="active", last_activity_days=40)
    (root / ".cron").mkdir()
    (root / ".cron" / "jobs.json").write_text(
        json.dumps([{"skills": "cr"}]),
        encoding="utf-8",
    )
    before = skill_dir.joinpath(".usage.json").read_bytes()

    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    assert {"skill": "cr", "reason": "cron"} in summary["skipped"]
    assert skill_dir.joinpath(".usage.json").read_bytes() == before


# ─── archive ─────────────────────────────────────────────────────────

def test_archive_moves_directory_and_updates_sidecar(tmp_path: Path) -> None:
    """``archive`` moves the dir to ``_archive/<cat>/<skill>/`` + state=archived."""
    root = _pack_empty(tmp_path)
    _skill(root, "arch", state="active", last_activity_days=2)

    result = SkillsRestore().archive("arch", as_root(root))
    assert result["archived"] is True
    assert result["archived_at"]

    archived = root / "_archive" / "cat" / "arch"
    assert (archived / "SKILL.md").is_file()
    assert not (root / "cat" / "arch").exists()
    record = _read_sidecar(archived)
    assert record["state"] == "archived"
    assert record["archived_at"] == result["archived_at"]


def test_second_archive_on_archived_skill_is_noop(tmp_path: Path) -> None:
    """A second ``archive`` on an already-archived skill is a no-op."""
    root = _pack_empty(tmp_path)
    _skill(root, "arch", state="active", last_activity_days=2)
    lifecycle = SkillsRestore()
    lifecycle.archive("arch", as_root(root))

    result = lifecycle.archive("arch", as_root(root))
    assert result == {
        "skill": "arch",
        "archived": False,
        "reason": "already-archived",
    }
    assert (root / "_archive" / "cat" / "arch" / "SKILL.md").is_file()


def test_archive_unknown_skill_raises(tmp_path: Path) -> None:
    root = _pack_empty(tmp_path)
    with pytest.raises(SkillNotFoundError):
        SkillsRestore().archive("nope", as_root(root))


def test_archive_occupied_slot_raises_conflict(tmp_path: Path) -> None:
    """Pre-existing ``_archive/<cat>/<skill>/`` slot → step 2 precondition
    fails → ``MutationConflictError`` and the source dir is untouched."""
    root = _pack_empty(tmp_path)
    skill_dir = _skill(root, "tx", state="active", last_activity_days=2)
    (root / "_archive" / "cat" / "tx").mkdir(parents=True)
    before_bytes = skill_dir.joinpath(".usage.json").read_bytes()

    with pytest.raises(MutationConflictError):
        SkillsRestore().archive("tx", as_root(root))

    assert (skill_dir / "SKILL.md").is_file()
    assert skill_dir.joinpath(".usage.json").read_bytes() == before_bytes
    assert _read_sidecar(skill_dir)["state"] == "active"


# ─── restore ─────────────────────────────────────────────────────────

def test_restore_moves_directory_back_and_reanchors(tmp_path: Path) -> None:
    """``restore`` moves the dir back + state=active + archived_at cleared + clock reanchored."""
    root = _pack_empty(tmp_path)
    _skill(root, "arch", state="active", last_activity_days=2)
    lifecycle = SkillsRestore()
    lifecycle.archive("arch", as_root(root))
    result = lifecycle.restore("arch", as_root(root))

    assert result == {"skill": "arch", "restored": True, "state": "active"}
    skill_dir = root / "cat" / "arch"
    assert (skill_dir / "SKILL.md").is_file()
    assert not (root / "_archive" / "cat" / "arch").exists()
    record = _read_sidecar(skill_dir)
    assert record["state"] == "active"
    assert record.get("archived_at") in ("", None)
    assert record["activity_window_start"] > _ago_iso(1)


def test_restore_of_non_archived_skill_is_noop(tmp_path: Path) -> None:
    root = _pack_empty(tmp_path)
    _skill(root, "plain", state="active", last_activity_days=2)
    result = SkillsRestore().restore("plain", as_root(root))
    assert result == {"skill": "plain", "restored": False, "reason": "not-archived"}


def test_restore_unknown_skill_raises(tmp_path: Path) -> None:
    root = _pack_empty(tmp_path)
    with pytest.raises(SkillNotFoundError):
        SkillsRestore().restore("nope", as_root(root))

# ─── two-step transaction rollback ──────────────────────────────────

def test_archive_rolls_back_on_second_step_failure(tmp_path: Path, monkeypatch) -> None:
    """Step-2 move failure rolls back step 1: dir stays put, prior state
    restored, ``MutationConflictError`` raised."""
    root = _pack_empty(tmp_path)
    skill_dir = _skill(root, "rb-a", state="stale")
    prior_state = _read_sidecar(skill_dir)["state"]

    import skills_design.src.capabilities_skills_restore as cap

    original_replace = cap.Path.replace

    def _replace(self, target):
        if self == skill_dir:
            raise OSError("injected second-step failure")
        return original_replace(self, target)

    monkeypatch.setattr(cap.Path, "replace", _replace)

    with pytest.raises(MutationConflictError):
        SkillsRestore().archive("rb-a", as_root(root))

    assert (root / "cat" / "rb-a").is_dir()
    assert not (root / "_archive" / "cat" / "rb-a").exists()
    assert _read_sidecar(root / "cat" / "rb-a")["state"] == prior_state


def test_restore_rolls_back_on_second_step_failure(tmp_path: Path, monkeypatch) -> None:
    """Step-2 move failure rolls back step 1: dir stays put, prior state
    restored, ``MutationConflictError`` raised."""
    root = _pack_empty(tmp_path)
    _skill(root, "arch-rb", state="active")
    result = SkillsRestore().archive("arch-rb", as_root(root))
    assert result["archived"] is True
    archived_dir = root / "_archive" / "cat" / "arch-rb"
    prior_state = _read_sidecar(archived_dir)["state"]

    import skills_design.src.capabilities_skills_restore as cap

    original_replace = cap.Path.replace

    def _replace(self, target):
        if self == archived_dir:
            raise OSError("injected second-step failure")
        return original_replace(self, target)

    monkeypatch.setattr(cap.Path, "replace", _replace)

    with pytest.raises(MutationConflictError):
        SkillsRestore().restore("arch-rb", as_root(root))

    assert archived_dir.is_dir()
    assert not (root / "cat" / "arch-rb").exists()
    assert _read_sidecar(archived_dir)["state"] == prior_state

# ─── apply_automatic_transitions: seeding ───────────────────────────

def test_missing_sidecar_is_seeded_before_transition(tmp_path: Path) -> None:
    """A skill with no ``.usage.json`` gets a baseline sidecar written
    on disk before any transition is evaluated."""
    root = _pack_empty(tmp_path)
    skill_dir = root / "cat" / "newborn"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: newborn\ndescription: x\n---\n",
        encoding="utf-8",
    )
    sidecar = skill_dir / ".usage.json"
    assert not sidecar.exists()

    summary = SkillsRunner().apply_automatic_transitions(as_root(root))

    assert sidecar.exists()
    record = _read_sidecar(skill_dir)
    assert record["state"] == "active"
    # The freshly seeded baseline anchors are all "now", so the pass
    # evaluates a no-op: nothing is applied, and the only skip entry is
    # the young-unused invariant, not a stale move.
    assert not [e for e in summary["applied"] if e["skill"] == "newborn"]
    skipped_newborn = [e for e in summary["skipped"] if e["skill"] == "newborn"]
    assert skipped_newborn == [{"skill": "newborn", "reason": "young-unused"}]


def test_restore_occupied_origin_raises_conflict(tmp_path: Path) -> None:
    """Pre-existing origin slot → step 2 precondition fails →
    ``MutationConflictError`` and the archived dir stays put."""
    root = _pack_empty(tmp_path)
    _skill(root, "txr", state="stale", last_activity_days=35)
    lifecycle = SkillsRestore()
    lifecycle.archive("txr", as_root(root))
    (root / "cat" / "txr").mkdir()
    archived_dir = root / "_archive" / "cat" / "txr"
    before_bytes = archived_dir.joinpath(".usage.json").read_bytes()

    with pytest.raises(MutationConflictError):
        lifecycle.restore("txr", as_root(root))

    assert (archived_dir / "SKILL.md").is_file()
    assert archived_dir.joinpath(".usage.json").read_bytes() == before_bytes
    assert _read_sidecar(archived_dir)["state"] == "archived"


# ─── config overlay ──────────────────────────────────────────────────

def test_config_overlay_stale_after_days(tmp_path: Path) -> None:
    """``.lifecycle_config.json`` with ``stale_after_days=7``: a 10-day-old
    record goes stale (would NOT under the default 14)."""
    root = _pack_empty(tmp_path)
    _skill(root, "ten", state="active", last_activity_days=10)
    (root / ".lifecycle_config.json").write_text(
        json.dumps({"stale_after_days": 7}),
        encoding="utf-8",
    )

    summary = SkillsRunner().apply_automatic_transitions(as_root(root))
    assert [entry for entry in summary["applied"] if entry["skill"] == "ten"] == [
        {"skill": "ten", "from": "active", "to": "stale"},
    ]
    assert _read_sidecar(root / "cat" / "ten")["state"] == "stale"

# ─── prune ──────────────────────────────────────────────────────────

def test_prune_bulk_archives_idle_skills(tmp_path: Path) -> None:
    """An idle skill past cutoff gets bulk-archived by prune."""
    root = _pack_empty(tmp_path)
    _skill(root, "old", state="active", last_activity_days=45)
    _skill(root, "new", state="active", last_activity_days=5)
    (root / ".lifecycle_config.json").write_text(
        json.dumps({"archive_after_days": 30}), encoding="utf-8"
    )

    result = SkillsPrune().prune(as_root(root))
    assert len(result["pruned"]) == 1
    assert result["pruned"][0]["skill"] == "old"
    assert any(k["skill"] == "new" for k in result["kept"])
    assert not (root / "cat" / "old").exists()
    assert (root / "_archive" / "cat" / "old" / "SKILL.md").exists()
    assert (root / "cat" / "new").exists()

def test_prune_refuses_days_less_than_one(tmp_path: Path) -> None:
    root = _pack_empty(tmp_path)
    with pytest.raises(ValueError, match="days must be >= 1"):
        SkillsPrune().prune(as_root(root), days=0)

def test_prune_keeps_pinned_stale_skill(tmp_path: Path) -> None:
    """Pinned skills are kept even when past the cutoff."""
    root = _pack_empty(tmp_path)
    _skill(root, "old", state="active", last_activity_days=45, pinned=True)
    (root / ".lifecycle_config.json").write_text(
        json.dumps({"archive_after_days": 30}), encoding="utf-8"
    )

    result = SkillsPrune().prune(as_root(root))
    assert result["pruned"] == []
    assert any(k["skill"] == "old" for k in result["kept"])
    assert (root / "cat" / "old").exists()

def test_prune_keeps_locked_stale_skill(tmp_path: Path) -> None:
    """Locked skills are kept even when past the cutoff."""
    root = _pack_empty(tmp_path)
    _skill(root, "old", state="active", last_activity_days=45, locked=True)
    (root / ".lifecycle_config.json").write_text(
        json.dumps({"archive_after_days": 30}), encoding="utf-8"
    )

    result = SkillsPrune().prune(as_root(root))
    assert result["pruned"] == []
    assert any(k["skill"] == "old" for k in result["kept"])
    assert (root / "cat" / "old").exists()


# ─── purge ──────────────────────────────────────────────────────────

def test_purge_deletes_archived_skill(tmp_path: Path) -> None:
    """Purge hard-deletes skill from _archive/."""
    root = _pack_empty(tmp_path)
    _skill(root, "victim", state="active", uses=3)
    lifecycle = SkillsRestore()
    lifecycle.archive("victim", as_root(root))
    archived_dir = root / "_archive" / "cat" / "victim"
    assert (archived_dir / "SKILL.md").exists()

    result = SkillsPurge().purge("victim", as_root(root))
    assert result == {
        "skill": "victim",
        "purged": True,
        "dry_run": False,
    }
    assert not archived_dir.exists()

def test_purge_unknown_skill(tmp_path: Path) -> None:
    """Purge of non-archived skill returns not-found without crashing."""
    root = _pack_empty(tmp_path)
    result = SkillsPurge().purge("nope", as_root(root))
    assert result == {"skill": "nope", "purged": False, "reason": "not-found-in-archive"}
