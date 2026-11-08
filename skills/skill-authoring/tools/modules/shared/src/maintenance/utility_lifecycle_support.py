"""Shared constants and pure helpers for skill lifecycle capabilities.

Holds the pack-file layout constants, the sidecar record shape, the
cross-platform lock primitives, the tarball-safety filter, and the
record/transition helpers used by the focused lifecycle capability
modules. The modules import from here; this module imports only shared
utilities and taxonomy, never a capability.
"""

from __future__ import annotations

import json
import os
import re
import tarfile
import time
from collections.abc import Iterable
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from shared.src.storage.utility_skill_pack import iter_skill_mds
from shared.src.maintenance.utility_skills_mutation import (
    archive_root,
    assert_within_root,
    atomic_write_json,
)
from shared.src.design.taxonomy_skills_constant import (
    ARCHIVE_DIRNAME,
    LIFECYCLE_STATES,
)
from shared.src.common.taxonomy_common_error import (
    MutationConflictError,
    SkillNotFoundError,
    SkillsUsageError,
)
from shared.src.design.taxonomy_skills_request import SkillsRoot
import shared.src.discovery.utility_discovery_core as _core

__all__ = [
    "ACTIVE",
    "ARCHIVED",
    "BACKUP_DIRNAME",
    "BLOBS_DIRNAME",
    "DEFAULT_CREATED_BY",
    "DEFAULT_KEEP",
    "DEFAULT_LEDGER_ACTOR",
    "DEFAULT_LEDGER_COMPACT_DAYS",
    "DEFAULT_STATE",
    "EXCLUDED_PATHS",
    "FIELDS",
    "LEDGER_FILENAME",
    "MANIFEST_NAME",
    "STALE",
    "TARBALL_NAME",
    "archive_skill",
    "find_skill_dir",
    "manifest_sha256",
    "now_iso",
    "read_record",
    "restore_skill",
    "set_field",
    "tar_data_filter",
    "write_record",
]

ACTIVE = LIFECYCLE_STATES[0]
STALE = LIFECYCLE_STATES[1]
ARCHIVED = LIFECYCLE_STATES[2]

FIELDS = (
    "state",
    "pinned",
    "created_by",
    "created_at",
    "first_seen_at",
    "last_activity_at",
    "archived_at",
    "views",
    "uses",
    "activity_window_start",
    "locked",
)

DEFAULT_STATE = "active"
DEFAULT_CREATED_BY = "agent"
DEFAULT_KEEP = 2
_DEFAULT_TIMESTAMP = ""

BACKUP_DIRNAME = ".lifecycle_backups"
TARBALL_NAME = "skills.tar.gz"
MANIFEST_NAME = "manifest.json"

LEDGER_FILENAME = ".lifecycle_ledger.jsonl"
BLOBS_DIRNAME = "blobs"
DEFAULT_LEDGER_ACTOR = "lifecycle"
DEFAULT_LEDGER_COMPACT_DAYS = 90

EXCLUDED_PATHS: frozenset[str] = frozenset(
    {
        BACKUP_DIRNAME,
        ".hub",
        ".locks",
        ".git",
        ".archive",
        ARCHIVE_DIRNAME,
        LEDGER_FILENAME,
        "venv",
        "node_modules",
    }
)
_CACHE_MARKERS: frozenset[str] = frozenset({"__pycache__"})


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _utc_iso_stamp(now: float | None = None) -> str:
    if now is None:
        now = time.time()
    return datetime.fromtimestamp(now, tz=UTC).isoformat().replace("+00:00", "")


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


def entry_ts(entry: dict) -> str:
    value = entry.get("ts")
    return value if isinstance(value, str) and value else ""

def _parse_ts(ts: str) -> float | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts).timestamp()
    except ValueError:
        return None

def _is_newer_than(entry: dict, days: int) -> bool:
    ts = entry_ts(entry)
    parsed = _parse_ts(ts)
    if parsed is None:
        return True
    cutoff = _parse_ts(now_iso()) - days * 86400
    return parsed >= cutoff


def _is_valid_sha256(digest: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", digest))


def manifest_sha256(manifest: Any) -> list[str]:
    seen: dict[str, None] = {}
    if isinstance(manifest, Iterable) and not isinstance(manifest, (str, bytes)):
        for item in manifest:
            if isinstance(item, dict):
                digest = item.get("sha256")
                if isinstance(digest, str) and digest and digest not in seen:
                    seen[digest] = None
    return list(seen)


def _blob_dir(root: Path | SkillsRoot) -> Path:
    return Path(root) / BACKUP_DIRNAME / BLOBS_DIRNAME


def _ledger_file(root: Path | SkillsRoot | None) -> Path:
    return Path(root) / LEDGER_FILENAME  # type: ignore[operator]


def _is_cache_dir(name: str) -> bool:
    return name == "__pycache__" or "cache" in name.lower()

def _is_excluded(rel: str) -> bool:
    parts = Path(rel).parts
    for part in parts:
        if part in EXCLUDED_PATHS:
            return True
        if _is_cache_dir(part):
            return True
    return False


def _new_snapshot_name(base: str, existing: set[str]) -> str:
    if base not in existing:
        return base
    counter = 1
    while f"{base}-{counter}" in existing:
        counter += 1
    return f"{base}-{counter}"


def _sha256_of(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _iter_pack_files(root: Path) -> list[tuple[str, Path]]:
    """(relative-path, absolute-path) rows for every non-excluded file."""
    rows: list[tuple[str, Path]] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        kept: list[str] = []
        for d in sorted(dirnames):
            if _is_excluded(d) or _is_cache_dir(d):
                continue
            kept.append(d)
        dirnames[:] = kept
        for name in sorted(filenames):
            if _is_excluded(name) or _is_cache_dir(name):
                continue
            abs_path = Path(dirpath) / name
            rel = abs_path.relative_to(root).as_posix()
            if _is_excluded(rel):
                continue
            rows.append((rel, abs_path))
    return rows


def _assert_member_safe(member: tarfile.TarInfo, target_root: Path) -> None:
    if os.path.isabs(member.name):
        raise SkillsUsageError(f"unsafe tarball member (absolute path): {member.name}")
    parts = Path(member.name).parts
    if ".." in parts:
        raise SkillsUsageError(f"unsafe tarball member (path traversal): {member.name}")
    target = target_root / Path(*parts)
    try:
        target.resolve().relative_to(target_root.resolve())
    except ValueError as exc:
        raise SkillsUsageError(f"unsafe tarball member escapes the pack root: {member.name}") from exc
    if member.issym() or member.islnk():
        link_target = member.linkname
        if os.path.isabs(link_target) or ".." in Path(link_target.lstrip("/")).parts:
            raise SkillsUsageError(f"unsafe tarball link target: {link_target}")
        link_path = target / link_target
        try:
            link_path.resolve().relative_to(target_root.resolve())
        except ValueError as exc:
            raise SkillsUsageError(f"unsafe tarball link target: {link_target}") from exc


def tar_data_filter(member: tarfile.TarInfo, dest_path: str) -> tarfile.TarInfo:
    _assert_member_safe(member, Path(dest_path))
    return member


def _usage_path(skill_dir: Path) -> Path:
    return skill_dir / ".usage.json"


def _read_sidecar(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _baseline_record() -> dict:
    now = _now_iso()
    return {
        "state": DEFAULT_STATE,
        "pinned": False,
        "created_by": DEFAULT_CREATED_BY,
        "created_at": now,
        "first_seen_at": now,
        "last_activity_at": now,
        "archived_at": _DEFAULT_TIMESTAMP,
        "views": 0,
        "uses": 0,
        "activity_window_start": now,
        "locked": False,
    }


def _normalize(raw: dict) -> dict:
    rec = _baseline_record()
    for field in FIELDS:
        if field in raw:
            rec[field] = raw[field]
    return rec


def _lock_path(usage_path: Path) -> Path:
    return usage_path.parent / ".usage.json.lock"

def _lock_file(handle: Any) -> None:
    _core.cross_process_lock(handle)

def _unlock_file(handle: Any) -> None:
    try:
        import fcntl as _fcntl

        _fcntl.flock(handle.fileno(), _fcntl.LOCK_UN)
    except ImportError:
        try:
            import msvcrt as _msvcrt

            _msvcrt.locking(handle.fileno(), _msvcrt.LK_UNLCK, (1 << 31) - 1)
        except ImportError:
            pass
def _with_lock(path: Path, fn: Any) -> None:
    try:
        handle = _lock_path(path).open("a+", encoding="utf-8")
    except OSError:
        fn()
        return
    try:
        _lock_file(handle)
        fn()
    finally:
        _unlock_file(handle)
        handle.close()


def _cron_referenced(pack_root: Path, skill_name: str) -> bool:
    jobs_file = pack_root.joinpath(".cron", "jobs.json")
    if not jobs_file.is_file():
        return False
    try:
        payload = json.loads(jobs_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    jobs = payload if isinstance(payload, list) else [payload]
    for job in jobs:
        if not isinstance(job, dict):
            continue
        for field in ("skills", "skill"):
            refs = job.get(field)
            if refs == skill_name:
                return True
            if isinstance(refs, str) and skill_name in refs.split(","):
                return True
            if isinstance(refs, (list, tuple)) and skill_name in refs:
                return True
    return False


# ─── Record / transition helpers ────────────────────────────────────


def find_skill_dir(skill: str, root: Path, in_archive: bool = False) -> Path | None:
    search_root = archive_root(root) if in_archive else root
    if not search_root.is_dir():
        return None
    matches: list[Path] = []
    for p in search_root.rglob("SKILL.md"):
        if not in_archive and ARCHIVE_DIRNAME in p.parts:
            continue
        if p.parent.name == skill:
            matches.append(p.parent)
    return min(matches) if matches else None


def read_record(skill_dir: Path) -> dict:
    return _read_sidecar(_usage_path(skill_dir))


def write_record(skill_dir: Path, record: dict) -> None:
    atomic_write_json(_usage_path(skill_dir), record)

def set_field(skill_dir: Path, field: str, value: object) -> None:
    record = read_record(skill_dir)
    record[field] = value
    write_record(skill_dir, record)

def set_state(skill_dir: Path, state: str, archived_at: str | None = None) -> None:
    record = read_record(skill_dir)
    record["state"] = state
    if archived_at is not None:
        record["archived_at"] = archived_at
    write_record(skill_dir, record)
def archive_skill(skill: str, pack_root: Path) -> dict:
    skill_dir = find_skill_dir(skill, pack_root, in_archive=False)
    if skill_dir is None:
        if find_skill_dir(skill, pack_root, in_archive=True) is not None:
            return {"skill": skill, "archived": False, "reason": "already-archived"}
        raise SkillNotFoundError(f"No skill directory found for: {skill}")

    category = skill_dir.parent.name
    destination = archive_root(pack_root) / category / skill
    assert_within_root(destination, pack_root)
    record = read_record(skill_dir)
    prior_state = record.get("state", "active")
    now_iso_val = _now_iso()

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise MutationConflictError(f"Archive slot already exists: {destination}")
    set_state(skill_dir, "archived", archived_at=now_iso_val)
    try:
        skill_dir.replace(destination)
    except OSError:
        record["state"] = prior_state
        record.pop("archived_at", None)
        write_record(skill_dir, record)
        raise MutationConflictError(
            f"Archive of {skill} failed mid-transaction; rolled back."
        ) from None

    return {"skill": skill, "archived": True, "archived_at": now_iso_val}


def restore_skill(skill: str, pack_root: Path, reanchor=None) -> dict:
    archived_dir = find_skill_dir(skill, pack_root, in_archive=True)
    if archived_dir is None:
        if find_skill_dir(skill, pack_root, in_archive=False) is None:
            raise SkillNotFoundError(f"No skill directory found for: {skill}")
        return {"skill": skill, "restored": False, "reason": "not-archived"}

    category = archived_dir.parent.name
    destination = pack_root / category / skill
    assert_within_root(destination, pack_root)
    record = read_record(archived_dir)
    prior_state = record.get("state", "archived")
    prior_archived_at = record.get("archived_at")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise MutationConflictError(f"Restore slot already exists: {destination}")

    record["state"] = "active"
    record.pop("archived_at", None)
    record["activity_window_start"] = _now_iso()
    write_record(archived_dir, record)
    try:
        archived_dir.replace(destination)
    except OSError:
        record["state"] = prior_state
        if prior_archived_at is not None:
            record["archived_at"] = prior_archived_at
        write_record(archived_dir, record)
        raise MutationConflictError(
            f"Restore of {skill} failed mid-transaction; rolled back."
        ) from None

    if reanchor is not None:
        reanchor(skill, pack_root)
    return {"skill": skill, "restored": True, "state": "active"}