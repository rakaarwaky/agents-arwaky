"""Lifecycle backup capability tests (snapshot + rollback, keep-knob, traversal).

Locks the two round-1 CRITICAL regressions:
* the safety-snapshot prune evicting the rollback target at the keep
  boundary (``test_rollback_to_older_snapshot_succeeds_at_keep_boundary``);
* path-traversal ids reaching the backup root
  (``test_rollback_rejects_traversal_id``, ``test_rollback_rejects_id_with_separator``).
"""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path

import pytest
from shared.src.skills_design.taxonomy_skills_error import (
    MutationConflictError,
    SkillsUsageError,
)
from shared.src.skills_design.utility_lifecycle_support import DEFAULT_KEEP

from skills_design.src.capabilities_skills_backup import SkillsBackup
from skills_design.src.capabilities_skills_rollback import SkillsRollback
from skills_design.tests.fixture_skills import crafted_tree


def _pair() -> tuple[SkillsBackup, SkillsRollback]:
    """A backup capability plus the rollback capability wired to it."""
    backup = SkillsBackup()
    return backup, SkillsRollback(backup)


def _snapshot_rollback(
    backup: SkillsBackup,
    rollback: SkillsRollback,
    root: Path,
    action: str,
    id_: str | None = None,
) -> dict:
    """Test-local dispatch over the split backup/rollback capabilities."""
    if action not in {"snapshot", "prune", "rollback"}:
        raise SkillsUsageError(f"unknown snapshot_rollback action: {action}")
    pack_root = Path(root)
    if action == "snapshot":
        snap = backup.create_snapshot(pack_root)
        return {"action": "snapshot", "snapshot": snap.name, "snapshot_dir": str(snap)}
    if action == "prune":
        removed = backup.prune_old_snapshots(pack_root)
        return {"action": "prune", "removed": [str(p) for p in removed]}
    return {"action": "rollback", **rollback.rollback(pack_root, id_)}


def _backup_dir(root: Path) -> Path:
    return root / ".lifecycle_backups"


def _snap_names(root: Path) -> list[str]:
    return sorted(p.name for p in _backup_dir(root).iterdir() if p.is_dir())


def _make_two_snapshots(root: Path) -> list[str]:
    """Two snapshots with distinct dir names, in creation order.

    The queue holds one extra name: the rollback's safety snapshot
    (taken later) pops it and sorts after both.
    """
    return _make_snapshots(root, 2)


def _make_snapshots(root: Path, count: int, safety: bool = True) -> list[str]:
    """``count`` snapshots with distinct dir names, in creation order.

    ``safety`` adds one extra queue entry so a rollback's safety snapshot
    (taken later, same patched stamp function) gets a name that sorts
    newest. Prune-only tests pass ``safety=False`` to keep exactly the
    ``count`` names.
    """
    names = [f"2026-01-01T00:{i:02d}:00" for i in range(count)]
    backup, _ = _pair()
    monkey = _stamp_sequence(*((names + [names[-1] + "-safety"]) if safety else names))
    try:
        for _ in names:
            backup.create_snapshot(root, _prune=False)
    finally:
        monkey.undo()
    return names


def _stamp_sequence(*stamps: str) -> pytest.MonkeyPatch:
    """Patch the module's ``_utc_iso_stamp`` to queue fixed distinct names.

    The queue drains; the last name repeats so a rollback's safety
    snapshot (a later call) still gets a name that sorts newest.
    """
    import skills_design.src.capabilities_skills_backup as mod

    queue = list(stamps)

    def _stamp(now=None):
        return queue.pop(0) if queue else stamps[-1]

    monkey = pytest.MonkeyPatch()
    monkey.setattr(mod, "_utc_iso_stamp", _stamp)
    return monkey


# ─── create_snapshot ───────────────────────────────────────────────


def test_create_snapshot_produces_tarball_and_manifest(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    backup, _rollback = _pair()
    snap = backup.create_snapshot(root)

    assert snap.parent == _backup_dir(root)
    tarball = snap / "skills.tar.gz"
    manifest_path = snap / "manifest.json"
    assert tarball.is_file()
    assert manifest_path.is_file()

    with tarfile.open(tarball, "r:gz") as tar:
        names = set(tar.getnames())
    assert "drafts/DESCRIPTION.md" in names
    assert "notes/note-taker/SKILL.md" in names

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "created_utc" in manifest
    files = manifest["files"]
    assert files, "manifest must list files"
    for row in files:
        assert set(row) == {"path", "sha256", "size"}
    by_path = {row["path"]: row for row in files}
    expected = (root / "drafts" / "DESCRIPTION.md").read_text(encoding="utf-8")
    assert by_path["drafts/DESCRIPTION.md"]["sha256"] == hashlib.sha256(
        expected.encode()
    ).hexdigest()
    assert by_path["drafts/DESCRIPTION.md"]["size"] == len(expected.encode())


def test_create_snapshot_excludes_excluded_paths(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    for name in [
        ".hub",
        ".locks",
        ".git",
        ".archive",
        "venv",
        "node_modules",
        "__pycache__",
    ]:
        d = root / name
        d.mkdir()
        (d / "junk.txt").write_text("x", encoding="utf-8")
    (root / ".lifecycle_ledger.jsonl").write_text("{}\n", encoding="utf-8")

    backup, _rollback = _pair()
    snap = backup.create_snapshot(root)
    with tarfile.open(snap / "skills.tar.gz", "r:gz") as tar:
        names = set(tar.getnames())

    for name in [
        ".hub",
        ".locks",
        ".git",
        ".archive",
        "venv",
        "node_modules",
        "__pycache__",
        ".lifecycle_ledger.jsonl",
    ]:
        assert not any(
            n == name or n.startswith(name + "/") for n in names
        ), f"{name} leaked into the tarball"
    assert "drafts/DESCRIPTION.md" in names


def test_create_snapshot_same_second_retake_gets_uniqueness_suffix(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    backup, _rollback = _pair()

    monkey = _stamp_sequence("2026-01-01T00:00:00")
    try:
        first = backup.create_snapshot(root, _prune=False)
        second = backup.create_snapshot(root, _prune=False)
    finally:
        monkey.undo()
    assert first.name == "2026-01-01T00:00:00"
    assert second.name == "2026-01-01T00:00:00-1"
    assert sorted(_snap_names(root)) == ["2026-01-01T00:00:00", "2026-01-01T00:00:00-1"]
    assert (first / "skills.tar.gz").is_file()
    assert (second / "skills.tar.gz").is_file()


# ─── prune_old_snapshots ───────────────────────────────────────────


def test_prune_old_snapshots_keeps_newest_keep(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    backup, _rollback = _pair()

    monkey = _stamp_sequence(
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:01",
        "2026-01-01T00:00:02",
        "2026-01-01T00:00:03",
    )
    try:
        backup.create_snapshot(root, _prune=False)
        backup.create_snapshot(root, _prune=False)
        backup.create_snapshot(root, _prune=False)
        backup.create_snapshot(root, _prune=False)

        (root / ".lifecycle_config.json").write_text(
            json.dumps({"backup": {"keep": 2}}), encoding="utf-8"
        )
        removed = backup.prune_old_snapshots(root)
        remaining = _snap_names(root)
    finally:
        monkey.undo()

    assert remaining == ["2026-01-01T00:00:02", "2026-01-01T00:00:03"]
    removed_names = [p.name for p in removed]
    assert removed_names == ["2026-01-01T00:00:01", "2026-01-01T00:00:00"]


def test_prune_old_snapshots_uses_config_backup_keep(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    backup, _rollback = _pair()
    monkey = _stamp_sequence(
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:01",
        "2026-01-01T00:00:02",
    )
    try:
        backup.create_snapshot(root, _prune=False)
        backup.create_snapshot(root, _prune=False)
        backup.create_snapshot(root, _prune=False)
        (root / ".lifecycle_config.json").write_text(
            json.dumps({"backup": {"keep": 1}}), encoding="utf-8"
        )
        removed = backup.prune_old_snapshots(root)
    finally:
        monkey.undo()

    assert [p.name for p in removed] == [
        "2026-01-01T00:00:01",
        "2026-01-01T00:00:00",
    ]
    assert _snap_names(root) == ["2026-01-01T00:00:02"]


def test_prune_old_snapshots_unset_config_falls_back_to_default_keep(
    tmp_path: Path,
) -> None:
    root = crafted_tree(tmp_path)
    backup, _rollback = _pair()
    monkey = _stamp_sequence(
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:01",
        "2026-01-01T00:00:02",
        "2026-01-01T00:00:03",
    )
    try:
        backup.create_snapshot(root, _prune=False)
        backup.create_snapshot(root, _prune=False)
        backup.create_snapshot(root, _prune=False)
        backup.create_snapshot(root, _prune=False)
        removed = backup.prune_old_snapshots(root)
    finally:
        monkey.undo()

    assert DEFAULT_KEEP == 2
    assert [p.name for p in removed] == ["2026-01-01T00:00:01", "2026-01-01T00:00:00"]
    assert _snap_names(root) == ["2026-01-01T00:00:02", "2026-01-01T00:00:03"]


# ─── rollback: critical keep-boundary regression ───────────────────


def test_rollback_to_older_snapshot_succeeds_at_keep_boundary(tmp_path: Path) -> None:
    """Round-1 CRITICAL: the safety snapshot's prune must not evict the target.

    2 snapshots, keep=2: rolling back to the OLDER one takes a safety
    snapshot (3 dirs total), and the prune of that safety snapshot must
    exclude the target dir or the target is evicted before it can be
    restored.
    """
    root = crafted_tree(tmp_path)
    _backup, rollback = _pair()
    names = _make_two_snapshots(root)
    (older, _) = names
    target_dir = _backup_dir(root) / older

    (root / "notes" / "note-taker" / "SKILL.md").write_text(
        "# mutated\n", encoding="utf-8"
    )
    assert (target_dir / "skills.tar.gz").is_file()

    (root / ".lifecycle_config.json").write_text(
        json.dumps({"backup": {"keep": 2}}), encoding="utf-8"
    )
    result = rollback.rollback(root, older)
    assert result["restored"] is True

    assert target_dir.is_dir(), "target snapshot dir was pruned before restore"
    restored = (root / "notes" / "note-taker" / "SKILL.md").read_text(encoding="utf-8")
    assert restored.startswith("---")  # restored content from the older snapshot
    # a safety snapshot was taken before the restore
    remaining = _snap_names(root)
    assert older in remaining
    assert remaining != names, "a safety snapshot was taken"


# ─── rollback: path-traversal regressions ──────────────────────────


def test_rollback_rejects_traversal_id(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    _make_two_snapshots(root)
    _backup, rollback = _pair()
    with pytest.raises(SkillsUsageError, match="invalid snapshot id"):
        rollback.rollback(root, "../../../../etc")


def test_rollback_rejects_id_with_separator(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    _make_two_snapshots(root)
    _backup, rollback = _pair()
    with pytest.raises(SkillsUsageError, match="invalid snapshot id"):
        rollback.rollback(root, "a/b")


def test_rollback_rejects_dotdot_only_id_escapes_backup_root(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    _make_two_snapshots(root)
    _backup, rollback = _pair()
    with pytest.raises(SkillsUsageError, match="escapes the backup root"):
        rollback.rollback(root, "..")


def test_rollback_rejects_unknown_snapshot_id(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    _make_two_snapshots(root)
    _backup, rollback = _pair()
    with pytest.raises(SkillsUsageError, match="unknown snapshot id"):
        rollback.rollback(root, "no-such-snapshot")


def test_rollback_with_no_snapshots_is_a_usage_error(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    _backup, rollback = _pair()
    with pytest.raises(SkillsUsageError, match="no snapshots"):
        rollback.rollback(root, None)


# ─── rollback happy path ────────────────────────────────────────────


def test_rollback_restores_modified_file_and_carries_excluded_subtrees(
    tmp_path: Path,
) -> None:
    root = crafted_tree(tmp_path)
    _backup, rollback = _pair()
    names = _make_two_snapshots(root)
    target = names[-1]

    # live tree mutates after the target snapshot
    skill_md = root / "notes" / "note-taker" / "SKILL.md"
    skill_md.write_text("# mutated\n", encoding="utf-8")
    hub = root / ".hub"
    hub.mkdir()
    (hub / "hub-lock.json").write_text("{}", encoding="utf-8")

    result = rollback.rollback(root, target)
    assert result["restored"] is True

    assert skill_md.read_text(encoding="utf-8").startswith("---")
    assert (hub / "hub-lock.json").is_file(), "excluded subtree not carried back"
    staging = root / f".rollback-staging-{target}"
    assert staging.is_dir(), "staging dir must stay on disk as the undo record"


def test_rollback_happy_path_via_explicit_id_and_dispatch(
    tmp_path: Path,
) -> None:
    root = crafted_tree(tmp_path)
    backup, rollback = _pair()
    names = _make_two_snapshots(root)
    target = names[0]
    out = _snapshot_rollback(backup, rollback, root, "rollback", target)
    assert out["action"] == "rollback"
    assert out["restored"] is True
    assert out["snapshot"] == target


# ─── rollback extract failure ──────────────────────────────────────


def test_rollback_corrupt_tarball_keeps_unrestored_and_raises(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    _backup, rollback = _pair()
    names = _make_two_snapshots(root)
    target = names[-1]
    target_dir = _backup_dir(root) / target

    (root / "notes" / "note-taker" / "SKILL.md").write_text("# mutated\n", encoding="utf-8")
    (target_dir / "skills.tar.gz").write_bytes(b"not a tarball")

    with pytest.raises(MutationConflictError, match="rollback to snapshot"):
        rollback.rollback(root, target)

    unrestored = root / f".rollback-unrestored-{target}"
    assert unrestored.is_dir(), "unstage record must be kept on failure"
    assert not (root / f".rollback-staging-{target}").exists()
    # un-stage put the live tree back (the unrestored record is separate)
    assert (root / "notes" / "note-taker" / "SKILL.md").is_file()


def test_rollback_extract_failure_with_traversal_member(tmp_path: Path) -> None:
    """A tarball member that walks outside the root is rejected explicitly."""
    root = crafted_tree(tmp_path)
    _backup, rollback = _pair()
    names = _make_two_snapshots(root)
    target = names[-1]
    target_dir = _backup_dir(root) / target

    import io

    buf = io.BytesIO()
    with tarfile.open(target_dir / "skills.tar.gz", "r:gz") as src, tarfile.open(
        fileobj=buf, mode="w:gz"
    ) as dst:
        for member in src.getmembers():
            if member.isdir():
                dst.addfile(member)
            else:
                dst.addfile(member, src.extractfile(member))
        info = tarfile.TarInfo("../../evil")
        dst.addfile(info, io.BytesIO(b"x"))
    buf.seek(0)
    target_dir.joinpath("skills.tar.gz").write_bytes(buf.read())

    with pytest.raises(MutationConflictError):
        rollback.rollback(root, target)
    assert (root / f".rollback-unrestored-{target}").is_dir()
    assert not (root.parent / "evil").exists()


# ─── dispatch ──────────────────────────────────────────────────────


def test_snapshot_rollback_dispatch_snapshot_and_prune(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    backup, rollback = _pair()
    out = _snapshot_rollback(backup, rollback, root, "snapshot")
    assert out["action"] == "snapshot"
    assert out["snapshot"] == out["snapshot_dir"].rsplit("/", 1)[-1]
    assert (Path(out["snapshot_dir"]) / "skills.tar.gz").is_file()

    out = _snapshot_rollback(backup, rollback, root, "prune")
    assert out["action"] == "prune"
    assert isinstance(out["removed"], list)


def test_snapshot_rollback_dispatch_unknown_action_is_usage_error(
    tmp_path: Path,
) -> None:
    root = crafted_tree(tmp_path)
    backup, rollback = _pair()
    with pytest.raises(SkillsUsageError, match="unknown snapshot_rollback action"):
        _snapshot_rollback(backup, rollback, root, "bogus")


def test_rollback_newest_snapshot_when_id_is_none(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    names = _make_two_snapshots(root)
    backup, rollback = _pair()
    out = _snapshot_rollback(backup, rollback, root, "rollback", None)
    assert out["action"] == "rollback"
    assert out["snapshot"] == names[-1]


def test_prune_old_snapshots_excluded_param_protects_a_named_dir(
    tmp_path: Path,
) -> None:
    root = crafted_tree(tmp_path)
    names = _make_snapshots(root, 4, safety=False)
    (root / ".lifecycle_config.json").write_text(
        json.dumps({"backup": {"keep": 2}}), encoding="utf-8"
    )
    backup, _rollback = _pair()
    removed = backup.prune_old_snapshots(root, excluded=frozenset({names[0]}))
    # keep=2: the two newest dirs (names[3], names[2]) survive; the excluded
    # oldest dir (names[0]) is protected; only names[1] is removed.
    assert [p.name for p in removed] == [names[1]]
    assert _snap_names(root) == [names[0], names[2], names[3]]


def test_rollback_carries_excluded_locks_subtree_back(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    _backup, rollback = _pair()
    names = _make_two_snapshots(root)
    target = names[-1]

    locks = root / ".locks"
    locks.mkdir()
    (locks / "skill.lock").write_text("pid", encoding="utf-8")
    (root / "notes" / "note-taker" / "SKILL.md").write_text("# mutated\n", encoding="utf-8")

    rollback.rollback(root, target)

    assert (locks / "skill.lock").is_file(), ".locks must be carried back"
    staging = root / f".rollback-staging-{target}"
    assert staging.is_dir(), "staging dir must remain as the undo record"


def test_snapshot_prune_removes_excess_when_keep_exceeded(tmp_path: Path) -> None:
    """create_snapshot prunes to keep after each take."""
    root = crafted_tree(tmp_path)
    backup, _rollback = _pair()
    (root / ".lifecycle_config.json").write_text(
        json.dumps({"backup": {"keep": 1}}), encoding="utf-8"
    )
    names = _make_snapshots(root, 1, safety=False)
    # a second take must leave only the newest
    backup.create_snapshot(root)
    remaining = _snap_names(root)
    assert len(remaining) == 1
    assert remaining[0] != names[0]


def test_manifest_has_no_keep_key_and_uses_utc_stamp(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    backup, _rollback = _pair()
    snap = backup.create_snapshot(root)
    manifest = json.loads((snap / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest) == {"created_utc", "files"}
    assert "keep" not in manifest
    assert manifest["created_utc"] == snap.name, "manifest must carry the snapshot stamp"


def test_create_snapshot_default_prunes_to_keep_after_take(tmp_path: Path) -> None:
    root = crafted_tree(tmp_path)
    backup, _rollback = _pair()
    names = _make_snapshots(root, 3, safety=False)
    (root / ".lifecycle_config.json").write_text(
        json.dumps({"backup": {"keep": 1}}), encoding="utf-8"
    )
    # a fourth take prunes to keep=1, so only the newest survives
    backup.create_snapshot(root)
    remaining = _snap_names(root)
    assert len(remaining) == 1
    assert remaining[0] not in names
