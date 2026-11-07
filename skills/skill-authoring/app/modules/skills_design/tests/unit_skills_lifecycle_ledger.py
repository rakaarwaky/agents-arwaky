"""Lifecycle audit-ledger capability tests (append, read, compact, rollback).

Covers the ledger round-trip, content-addressed blob dedup, missing/torn
ledger reads, compact trimming + blob GC, the ``pre-rollback``/
``rollback`` pair (happy + fails-closed), and the ``actor`` default.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from shared.src.skills_design.taxonomy_skills_error import (
    MutationConflictError,
    SkillsUsageError,
)

from skills_design.src.capabilities_skills_lifecycle import (
    BLOBS_DIRNAME,
    DEFAULT_LEDGER_ACTOR,
    LEDGER_FILENAME,
    SkillsLifecycle,
)
from skills_design.tests.fixture_skills import as_root, crafted_tree

LEDGER = SkillsLifecycle()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _iso(delta_days: int = 0) -> str:
    return (datetime.now(UTC) - timedelta(days=delta_days)).isoformat(
        timespec="microseconds"
    )


def _blobs(root: Path) -> Path:
    return root / ".lifecycle_backups" / BLOBS_DIRNAME


def _blob_names(root: Path) -> list[str]:
    dir = _blobs(root)
    return sorted(p.name for p in dir.iterdir() if p.is_file()) if dir.is_dir() else []


def _ledger_file(root: Path) -> Path:
    return root / LEDGER_FILENAME


def _entry(
    skill: str,
    action: str,
    before: list | None = None,
    after: list | None = None,
    evidence: dict | None = None,
) -> dict:
    return {
        "action": action,
        "skill": skill,
        "before": before or [],
        "after": after or [],
        "evidence": evidence or {},
    }


def test_ledger_append_and_read_roundtrip(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    for i in range(3):
        stored = LEDGER.ledger_append(root, _entry(f"skill-{i}", "patch"))
        assert stored["action"] == "patch"
        assert stored["id"]

    entries = LEDGER.ledger_read(root)
    assert len(entries) == 3
    ids = [e["id"] for e in entries]
    assert len(set(ids)) == 3  # distinct uuid4 ids
    ts = [e["ts"] for e in entries]
    assert ts == sorted(ts)  # monotonic, oldest-first


def test_content_addressed_blob_dedup(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    target = Path(root) / "drafts" / "doc-drafts" / "SKILL.md"
    digest = _sha256(target.read_bytes())
    manifest = [{"path": str(target), "sha256": digest}]

    LEDGER.ledger_append(root, _entry("doc-drafts", "patch", after=manifest))
    assert (_blobs(root) / digest).is_file()
    count_after_first = len(_blob_names(root))

    LEDGER.ledger_append(root, _entry("doc-drafts", "patch", after=manifest))
    assert len(_blob_names(root)) == count_after_first  # dedup: no second blob


def _files_outside_ledger_and_blobs(root: Path) -> frozenset[str]:
    ledger = root / LEDGER_FILENAME
    blobs = _blobs(root)
    return frozenset(
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and p != ledger and blobs not in p.parents
    )


def test_ledger_append_rejects_path_traversal_sha256(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    target = Path(root) / "drafts" / "doc-drafts" / "SKILL.md"
    real_digest = _sha256(target.read_bytes())
    malicious_digest = "../../etc/passwd"
    before = _files_outside_ledger_and_blobs(root)
    manifest = [
        {"path": str(target), "sha256": real_digest},
        {"path": str(target), "sha256": malicious_digest},
    ]
    with pytest.raises(SkillsUsageError) as exc_info:
        LEDGER.ledger_append(root, _entry("doc-drafts", "patch", after=manifest))
    assert malicious_digest in str(exc_info.value)
    after = _files_outside_ledger_and_blobs(root)
    assert after == before  # nothing new outside ledger + blobs


def test_ledger_append_rejects_non_hex_sha256(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    target = Path(root) / "drafts" / "doc-drafts" / "SKILL.md"
    real_digest = _sha256(target.read_bytes())
    bad_digest = "z" * 64
    before = _files_outside_ledger_and_blobs(root)
    manifest = [
        {"path": str(target), "sha256": real_digest},
        {"path": str(target), "sha256": bad_digest},
    ]
    with pytest.raises(SkillsUsageError) as exc_info:
        LEDGER.ledger_append(root, _entry("doc-drafts", "patch", after=manifest))
    assert bad_digest in str(exc_info.value)
    after = _files_outside_ledger_and_blobs(root)
    assert after == before  # nothing new outside ledger + blobs


def test_ledger_read_missing_file_returns_empty(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    assert LEDGER.ledger_read(root) == ()


def test_ledger_read_drops_torn_trailing_line(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    stored = LEDGER.ledger_append(root, _entry("torn", "patch"))
    with _ledger_file(root).open("a", encoding="utf-8") as handle:
        handle.write('{"id": "partial", "ts": "incomplete\n')

    entries = LEDGER.ledger_read(root)
    assert len(entries) == 1
    assert entries[0]["id"] == stored["id"]


def test_ledger_compact_trims_old_entries_and_gcs_orphan_blobs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = as_root(crafted_tree(tmp_path))
    old_digest = _sha256(b"old content\n")
    new_digest = _sha256(b"new content\n")
    # Materialize both blobs in the store so GC has something to remove.
    blobs = _blobs(root)
    blobs.mkdir(parents=True, exist_ok=True)
    (blobs / old_digest).write_bytes(b"old content\n")
    (blobs / new_digest).write_bytes(b"new content\n")

    # Seed a backdated (5 days) entry referencing only the old blob.
    old_entry = _entry("old-skill", "patch", after=[{"path": "x", "sha256": old_digest}])
    old_entry["ts"] = _iso(5)
    # Seed a fresh entry referencing only the new blob.
    new_entry = _entry("new-skill", "patch", after=[{"path": "y", "sha256": new_digest}])
    _append_raw(root, old_entry, new_entry)

    monkeypatch.setattr(
        "skills_design.src.capabilities_skills_lifecycle.DEFAULT_LEDGER_COMPACT_DAYS",
        1,
    )
    result = LEDGER.ledger_compact(root)

    surviving = LEDGER.ledger_read(root)
    assert [e["skill"] for e in surviving] == ["new-skill"]
    assert result["entries_before"] == 2
    assert result["entries_after"] == 1
    assert result["blobs_garbage_collected"] == [old_digest]
    blob_names = _blob_names(root)
    assert old_digest not in blob_names  # GC'd
    assert new_digest in blob_names  # retained


def _append_raw(root: Path, *entries: dict) -> None:
    with _ledger_file(root).open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")


def test_rollback_entry_happy_path(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    target_file = Path(root) / "drafts" / "doc-drafts" / "SKILL.md"
    digest = _sha256(target_file.read_bytes())

    pre = LEDGER.ledger_append(
        root,
        _entry(
            "doc-drafts",
            "pre-rollback",
            after=[{"path": str(target_file), "sha256": digest}],
        ),
    )
    result = LEDGER.rollback_entry(root, pre["id"])

    assert result == {
        "rolled_back": True,
        "entry_id": pre["id"],
        "restored_files": [str(target_file)],
    }
    entries = LEDGER.ledger_read(root)
    rollback = [e for e in entries if e["action"] == "rollback"]
    assert len(rollback) == 1
    assert rollback[0]["evidence"]["rollback_target"] == pre["id"]


def test_rollback_entry_fails_closed_on_missing_blob(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    live = Path(root) / "drafts" / "doc-drafts" / "SKILL.md"
    before_bytes = live.read_bytes()
    # A manifest digest that no materialized blob matches: its source file
    # exists but carries different bytes, so ``ledger_append``'s content
    # check skips the copy and the safety capture stays absent.
    fake_digest = "0" * 64

    pre = LEDGER.ledger_append(
        root,
        _entry(
            "doc-drafts",
            "pre-rollback",
            after=[{"path": str(live), "sha256": fake_digest}],
        ),
    )
    assert not (_blobs(root) / fake_digest).is_file()
    with pytest.raises(MutationConflictError) as exc_info:
        LEDGER.rollback_entry(root, pre["id"])
    assert f"{BLOBS_DIRNAME}/{fake_digest}" in str(exc_info.value)
    assert live.read_bytes() == before_bytes  # live tree untouched


def test_actor_default_from_config(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    stored = LEDGER.ledger_append(root, _entry("doc-drafts", "patch"))
    assert stored["actor"] == DEFAULT_LEDGER_ACTOR


def test_actor_explicit_override(tmp_path: Path) -> None:
    root = as_root(crafted_tree(tmp_path))
    entry = _entry("doc-drafts", "patch")
    entry["actor"] = "user"
    override = LEDGER.ledger_append(root, entry)
    assert override["actor"] == "user"
