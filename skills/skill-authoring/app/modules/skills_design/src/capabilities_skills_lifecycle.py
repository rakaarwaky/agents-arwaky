"""Skills lifecycle capability (AES capabilities layer).

Unified lifecycle, telemetry, backup, and audit-ledger capabilities for
skills packs.

Public API:
    SkillsLifecycle
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import tarfile
import time
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows has no fcntl
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX has no msvcrt
    msvcrt = None

from shared.src.common.utility_skill_pack import default_pack_root, iter_skill_mds
from shared.src.common.utility_skills_mutation import (
    archive_root,
    assert_within_root,
    atomic_write_json,
)
from shared.src.skills_design.taxonomy_skills_constant import ARCHIVE_DIRNAME
from shared.src.skills_design.taxonomy_skills_error import (
    MutationConflictError,
    SkillNotFoundError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.skills_design.taxonomy_skills_lifecycle_config_vo import (
    load_lifecycle_config,
)
from shared.src.skills_design.taxonomy_skills_lifecycle_vo import LIFECYCLE_STATES
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot

__all__ = [
    "BACKUP_DIRNAME",
    "BLOBS_DIRNAME",
    "DEFAULT_KEEP",
    "DEFAULT_LEDGER_ACTOR",
    "DEFAULT_LEDGER_COMPACT_DAYS",
    "DEFAULT_STATE",
    "FIELDS",
    "LEDGER_FILENAME",
    "MANIFEST_NAME",
    "SkillsLifecycle",
    "TARBALL_NAME",
    "entry_ts",
    "manifest_sha256",
    "now_iso",
    "tar_data_filter",
]

logger = logging.getLogger(__name__)

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

def _iso_now() -> str:
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

def _skill_dirs(root: Path) -> Iterable[Path]:
    for md in iter_skill_mds(root):
        yield md.parent

def _usage_path(skill_dir: Path) -> Path:
    return skill_dir / ".usage.json"

def _lock_path(usage_path: Path) -> Path:
    return usage_path.parent / ".usage.json.lock"

def _read_sidecar(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}

def _baseline_record() -> dict:
    now = _iso_now()
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

def _lock_file(handle: Any) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    elif msvcrt is not None:
        handle.flush()
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1 << 31 - 1)

def _unlock_file(handle: Any) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    elif msvcrt is not None:
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1 << 31 - 1)
        except OSError:
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

class SkillsLifecycle:
    """Unified skill lifecycle capability: transitions, telemetry, backup, ledger."""

    # ─── Telemetry ─────────────────────────────────────────────────────

    def seed_record_if_missing(self, skill: str, root: SkillsRoot) -> None:
        skills_root = Path(root)
        skill_dir = self._resolve_skill_dir(skill, skills_root)
        if skill_dir is None:
            return
        path = _usage_path(skill_dir)

        def work() -> None:
            record = _read_sidecar(path)
            if record:
                return
            try:
                atomic_write_json(path, _baseline_record())
            except OSError:
                pass

        _with_lock(path, work)

    def reanchor_clock(self, skill: str, root: SkillsRoot) -> None:
        skills_root = Path(root)
        skill_dir = self._resolve_skill_dir(skill, skills_root)
        if skill_dir is None:
            return
        path = _usage_path(skill_dir)

        def work() -> None:
            record = _read_sidecar(path)
            if record:
                record = _normalize(record)
            else:
                record = _baseline_record()
            now = _iso_now()
            record["last_activity_at"] = now
            record["activity_window_start"] = now
            if not record.get("pinned", False):
                record["state"] = DEFAULT_STATE
            try:
                atomic_write_json(path, record)
            except OSError:
                pass

        _with_lock(path, work)

    def curated_report(self, root: SkillsRoot) -> list[dict]:
        skills_root = Path(root)
        rows: list[tuple[str, dict]] = []
        for skill_dir in _skill_dirs(skills_root):
            self.seed_record_if_missing(skill_dir.name, skills_root)
            record = _read_sidecar(_usage_path(skill_dir))
            rows.append(
                (skill_dir.name, _normalize(record) if record else _baseline_record())
            )
        rows.sort(key=lambda item: item[0])
        return [record for _name, record in rows]

    def view(self, skill: str, root: SkillsRoot) -> None:
        self._bump(skill, root, "views")

    def use(self, skill: str, root: SkillsRoot) -> None:
        self._bump(skill, root, "uses")

    def use_with_timestamp(self, skill: str, root: SkillsRoot, now_iso: str | None = None) -> None:
        self._bump(skill, root, "uses", now_iso=now_iso)

    def _resolve_skill_dir(self, skill: str, root: Path, in_archive: bool = False) -> Path | None:
        return self._find_skill_dir(skill, root, in_archive=in_archive)

    def _bump(self, skill: str, root: SkillsRoot, counter_field: str, now_iso: str | None = None) -> None:
        skills_root = Path(root)
        skill_dir = self._resolve_skill_dir(skill, skills_root)
        if skill_dir is None:
            return
        path = _usage_path(skill_dir)

        def work() -> None:
            record = _read_sidecar(path)
            if record:
                record = _normalize(record)
            else:
                record = _baseline_record()
            current_count = record.get(counter_field, 0)
            record[counter_field] = (current_count if isinstance(current_count, int) else 0) + 1
            now = now_iso or _iso_now()
            record["last_activity_at"] = now
            record["activity_window_start"] = now
            if not record.get("pinned", False):
                record["state"] = DEFAULT_STATE
            try:
                atomic_write_json(path, record)
            except OSError:
                pass

        _with_lock(path, work)

    # ─── Lifecycle transitions ─────────────────────────────────────────

    def apply_automatic_transitions(self, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        config = load_lifecycle_config(pack_root)
        now = datetime.now(UTC)
        stale_cutoff = now - timedelta(days=config.stale_after_days)
        archive_cutoff = now - timedelta(days=config.archive_after_days)
        applied: list[dict] = []
        skipped: list[dict] = []
        counts: dict[str, int] = {state: 0 for state in LIFECYCLE_STATES}

        for skill_md in iter_skill_mds(pack_root):
            name = skill_md.parent.name
            self.seed_record_if_missing(name, SkillsRoot(pack_root))
            record = self._read_record(skill_md.parent)
            state = record.get("state", ACTIVE)
            if state not in LIFECYCLE_STATES:
                state = ACTIVE
            counts[state] += 1

            if record.get("pinned", False):
                skipped.append({"skill": name, "reason": "pinned"})
                continue
            if record.get("locked", False):
                skipped.append({"skill": name, "reason": "locked"})
                continue
            if _cron_referenced(pack_root, name):
                skipped.append({"skill": name, "reason": "cron"})
                continue

            anchor = _parse_iso(record.get("last_activity_at"))
            if anchor is None:
                skipped.append({"skill": name, "reason": "no-anchor"})
                continue

            if record.get("uses", 0) == 0:
                created = _parse_iso(record.get("created_at"))
                if created is not None and created > stale_cutoff:
                    skipped.append({"skill": name, "reason": "young-unused"})
                    continue

            window_start = _parse_iso(record.get("activity_window_start"))
            if state == STALE and window_start is not None and window_start > stale_cutoff:
                self.reanchor_clock(name, SkillsRoot(pack_root))
                counts[STALE] -= 1
                counts[ACTIVE] += 1
                applied.append({"skill": name, "from": STALE, "to": ACTIVE})
            elif anchor <= archive_cutoff:
                record["state"] = ARCHIVED
                record["archived_at"] = _now_iso()
                self._write_record(skill_md.parent, record)
                counts[state] -= 1
                counts[ARCHIVED] += 1
                applied.append({"skill": name, "from": state, "to": ARCHIVED})
            elif anchor <= stale_cutoff and state == ACTIVE:
                record["state"] = STALE
                self._write_record(skill_md.parent, record)
                counts[ACTIVE] -= 1
                counts[STALE] += 1
                applied.append({"skill": name, "from": ACTIVE, "to": STALE})

        return {"applied": applied, "skipped": skipped, "state_counts": counts}

    def archive(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        skill_dir = self._find_skill_dir(skill, pack_root, in_archive=False)
        if skill_dir is None:
            if self._find_skill_dir(skill, pack_root, in_archive=True) is not None:
                return {
                    "skill": skill,
                    "archived": False,
                    "reason": "already-archived",
                }
            raise SkillNotFoundError(f"No skill directory found for: {skill}")

        category = skill_dir.parent.name
        destination = archive_root(pack_root) / category / skill
        assert_within_root(destination, pack_root)
        record = self._read_record(skill_dir)
        prior_state = record.get("state", ACTIVE)
        now_iso_val = _now_iso()

        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise MutationConflictError(
                f"Archive slot already exists: {destination}"
            )
        record["state"] = ARCHIVED
        record["archived_at"] = now_iso_val
        self._write_record(skill_dir, record)
        try:
            skill_dir.replace(destination)
        except OSError:
            record["state"] = prior_state
            record.pop("archived_at", None)
            self._write_record(skill_dir, record)
            raise MutationConflictError(
                f"Archive of {skill} failed mid-transaction; rolled back."
            ) from None

        return {"skill": skill, "archived": True, "archived_at": now_iso_val}

    def restore(self, skill: str, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        archived_dir = self._find_skill_dir(skill, pack_root, in_archive=True)
        if archived_dir is None:
            if self._find_skill_dir(skill, pack_root, in_archive=False) is None:
                raise SkillNotFoundError(f"No skill directory found for: {skill}")
            return {"skill": skill, "restored": False, "reason": "not-archived"}

        category = archived_dir.parent.name
        destination = pack_root / category / skill
        assert_within_root(destination, pack_root)
        record = self._read_record(archived_dir)
        prior_state = record.get("state", ARCHIVED)
        prior_archived_at = record.get("archived_at")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise MutationConflictError(
                f"Restore slot already exists: {destination}"
            )

        record["state"] = ACTIVE
        record.pop("archived_at", None)
        record["activity_window_start"] = _now_iso()
        self._write_record(archived_dir, record)
        try:
            archived_dir.replace(destination)
        except OSError:
            record["state"] = prior_state
            if prior_archived_at is not None:
                record["archived_at"] = prior_archived_at
            self._write_record(archived_dir, record)
            raise MutationConflictError(
                f"Restore of {skill} failed mid-transaction; rolled back."
            ) from None

        self.reanchor_clock(skill, SkillsRoot(pack_root))
        return {"skill": skill, "restored": True, "state": ACTIVE}

    def _find_skill_dir(self, skill: str, root: Path, in_archive: bool = False) -> Path | None:
        search_root = archive_root(root) if in_archive else root
        if not search_root.is_dir():
            return None
        matches: list[Path] = []
        for p in search_root.rglob("SKILL.md"):
            if not in_archive and ARCHIVE_DIRNAME in p.parts:
                continue
            if p.parent.name == skill:
                matches.append(p.parent)
        return sorted(matches)[0] if matches else None

    def _read_record(self, skill_dir: Path) -> dict:
        return _read_sidecar(_usage_path(skill_dir))

    def _write_record(self, skill_dir: Path, record: dict) -> None:
        atomic_write_json(_usage_path(skill_dir), record)

    def prune(
        self,
        root: SkillsRoot | None = None,
        days: int | None = None,
        dry_run: bool = False,
    ) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        config = load_lifecycle_config(pack_root)
        effective_days = days if days is not None else config.archive_after_days
        if effective_days < 1:
            raise ValueError(f"prune days must be >= 1, got {effective_days}")

        cutoff = datetime.now(UTC) - timedelta(days=effective_days)
        pruned: list[dict] = []
        kept: list[dict] = []

        for skill_md in iter_skill_mds(pack_root):
            skill_dir = skill_md.parent
            name = skill_dir.name
            record = self._read_record(skill_dir)
            state = record.get("state", ACTIVE)

            if record.get("pinned") or record.get("locked"):
                kept.append({"skill": name, "state": state, "reason": "pinned-or-locked"})
                continue

            if _cron_referenced(pack_root, name):
                kept.append({"skill": name, "state": state, "reason": "cron-referenced"})
                continue

            ts_str = (
                record.get("last_activity_at")
                or record.get("last_used_at")
                or record.get("last_viewed_at")
                or record.get("created_at")
            )
            is_idle = False
            if ts_str:
                dt = _parse_iso(ts_str)
                if dt is not None and dt <= cutoff:
                    is_idle = True
            else:
                is_idle = True

            if is_idle:
                if not dry_run:
                    self.archive(name, SkillsRoot(pack_root))
                pruned.append({"skill": name, "days_idle": effective_days})
            else:
                kept.append({"skill": name, "state": state})

        return {"pruned": pruned, "kept": kept, "dry_run": dry_run}

    def purge(
        self,
        skill: str | None = None,
        root: SkillsRoot | None = None,
        dry_run: bool = False,
    ) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        config = load_lifecycle_config(pack_root)

        if skill is not None:
            skill_dir = self._find_skill_dir(skill, pack_root, in_archive=True)
            if skill_dir is None:
                return {"skill": skill, "purged": False, "reason": "not-found-in-archive"}
            if not dry_run:
                shutil.rmtree(skill_dir, ignore_errors=True)
            return {"skill": skill, "purged": True, "dry_run": dry_run}

        ttl_days = getattr(config, "archive_ttl_days", 0)
        if ttl_days <= 0:
            return {"purged": [], "kept": [], "reason": "archive_ttl_days disabled"}

        cutoff = datetime.now(UTC) - timedelta(days=ttl_days)
        arch_root = archive_root(pack_root)
        if not arch_root.is_dir():
            return {"purged": [], "kept": []}

        purged: list[dict] = []
        kept: list[dict] = []

        for skill_md in iter_skill_mds(arch_root):
            skill_dir = skill_md.parent
            name = skill_dir.name
            record = self._read_record(skill_dir)
            archived_at = record.get("archived_at")
            mtime = datetime.fromtimestamp(skill_dir.stat().st_mtime, tz=UTC)
            dt = _parse_iso(archived_at) if archived_at else mtime
            cmp_dt = max(dt, mtime) if dt else mtime
            if cmp_dt <= cutoff:
                if not dry_run:
                    shutil.rmtree(skill_dir, ignore_errors=True)
                purged.append({"skill": name, "archived_at": str(archived_at)})
            else:
                kept.append({"skill": name, "archived_at": str(archived_at)})

        return {"purged": purged, "kept": kept, "dry_run": dry_run}

    # ─── Backup & rollback ─────────────────────────────────────────────

    def snapshot_rollback(
        self,
        root: SkillsRoot,
        action: str,
        id_: str | None = None,
    ) -> dict:
        """Dispatch ``action`` to the snapshot / prune / rollback verbs."""
        if action not in {"snapshot", "prune", "rollback"}:
            raise SkillsUsageError(f"unknown snapshot_rollback action: {action}")
        skills_root = Path(root)
        if action == "snapshot":
            snap = self.create_snapshot(skills_root)
            return {"action": "snapshot", "snapshot": snap.name, "snapshot_dir": str(snap)}
        if action == "prune":
            removed = self.prune_old_snapshots(skills_root)
            return {"action": "prune", "removed": [str(p) for p in removed]}
        return {"action": "rollback", **self.rollback(skills_root, id_)}

    def create_snapshot(self, root: Path, *, _prune: bool = True) -> Path:
        skills_root = self._require_root(root)
        backup_root = self._backup_root(skills_root)
        base = _utc_iso_stamp()
        existing = {p.name for p in backup_root.iterdir() if p.is_dir()}
        snap_dir = backup_root / _new_snapshot_name(base, existing)
        snap_dir.mkdir(parents=True)

        manifest_files: list[dict] = []
        tarball = snap_dir / TARBALL_NAME
        with tarfile.open(tarball, "w:gz") as tar:
            for rel, abs_path in _iter_pack_files(skills_root):
                info = tar.gettarinfo(str(abs_path), arcname=rel)
                if abs_path.is_dir():
                    tar.addfile(info)
                else:
                    tar.addfile(info, abs_path.open("rb"))
                manifest_files.append(
                    {"path": rel, "sha256": _sha256_of(abs_path), "size": abs_path.stat().st_size}
                )
        manifest = {"created_utc": snap_dir.name, "files": manifest_files}
        (snap_dir / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if _prune:
            self.prune_old_snapshots(skills_root)
        return snap_dir

    def prune_old_snapshots(
        self, root: Path, *, excluded: frozenset[str] | None = None
    ) -> list[Path]:
        skills_root = self._require_root(root)
        keep = self._keep_count(skills_root)
        excluded = excluded or frozenset()
        snap_dirs = sorted(
            (p for p in self._backup_root(skills_root).iterdir() if p.is_dir()),
            key=lambda p: p.name,
            reverse=True,
        )
        removable = [d for d in snap_dirs if d.name not in excluded]
        removed: list[Path] = []
        for snap in removable[keep:]:
            shutil.rmtree(snap)
            removed.append(snap)
        return removed

    def rollback(self, root: Path, id_: str | None = None) -> dict:
        skills_root = self._require_root(root)
        target = self._resolve_snapshot(skills_root, id_)
        target_name = target.name

        self.create_snapshot(skills_root, _prune=False)
        self.prune_old_snapshots(skills_root, excluded=frozenset({target_name}))

        staging = skills_root / f".rollback-staging-{target_name}"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()
        for entry in sorted(skills_root.iterdir()):
            if entry.name == BACKUP_DIRNAME or entry.name.startswith(".rollback-"):
                continue
            shutil.move(str(entry), str(staging / entry.name))

        tarball = target / TARBALL_NAME
        try:
            with tarfile.open(tarball, "r:gz") as tar:
                for member in tar:
                    _assert_member_safe(member, skills_root)
                tar.extractall(skills_root, filter=tar_data_filter)
        except Exception:
            logger.exception("snapshot extract failed; restoring staged tree")
            manifest = self._read_manifest(target)
            for row in manifest.get("files", []):
                leaked = skills_root / row["path"]
                try:
                    if leaked.is_dir():
                        shutil.rmtree(leaked, ignore_errors=True)
                    elif leaked.exists():
                        leaked.unlink()
                except OSError:
                    pass
            try:
                for entry in sorted(staging.iterdir()):
                    destination = skills_root / entry.name
                    if destination.exists():
                        continue
                    shutil.move(str(entry), str(destination))
            except Exception:
                logger.exception("unstage failed; keeping the staged entries")
            unrestored = skills_root / f".rollback-unrestored-{target_name}"
            if unrestored.exists():
                shutil.rmtree(unrestored)
            shutil.move(str(staging), str(unrestored))
            raise MutationConflictError(
                f"rollback to snapshot {target_name!r} failed; "
                f"staged tree preserved under .rollback-unrestored-{target_name}"
            ) from None

        for entry in sorted(staging.iterdir()):
            if (skills_root / entry.name).exists():
                continue
            shutil.move(str(entry), str(skills_root / entry.name))

        return {
            "snapshot": target_name,
            "staging": str(staging),
            "restored": True,
        }

    def _require_root(self, root: Path) -> Path:
        p = Path(root)
        if not p.is_dir():
            raise SkillsRootError(f"skills root does not exist: {p}")
        return p

    def _backup_root(self, skills_root: Path) -> Path:
        d = skills_root / BACKUP_DIRNAME
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _keep_count(self, skills_root: Path) -> int:
        config = load_lifecycle_config(skills_root)
        val = getattr(config, "backup_keep", DEFAULT_KEEP)
        return val if isinstance(val, int) and val > 0 else DEFAULT_KEEP

    def _resolve_snapshot(self, skills_root: Path, id_: str | None) -> Path:
        backup_root = self._backup_root(skills_root)
        if id_ is None:
            snaps = [p for p in backup_root.iterdir() if p.is_dir()]
            if not snaps:
                raise SkillsUsageError("no snapshots to roll back to")
            return max(snaps, key=lambda p: p.name)
        if "/" in id_ or os.sep in id_:
            raise SkillsUsageError(f"invalid snapshot id: {id_}")
        snap = backup_root / id_
        if ".." in snap.parts:
            raise SkillsUsageError(f"snapshot id escapes the backup root: {id_}")
        try:
            snap.resolve().relative_to(backup_root.resolve())
        except ValueError as exc:
            raise SkillsUsageError(f"snapshot id escapes the backup root: {id_}") from exc
        if not snap.is_dir():
            raise SkillsUsageError(f"unknown snapshot id: {id_}")
        return snap

    def _read_manifest(self, snap_dir: Path) -> dict:
        manifest_file = snap_dir / MANIFEST_NAME
        if not manifest_file.is_file():
            return {}
        try:
            return json.loads(manifest_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    # ─── Audit ledger ──────────────────────────────────────────────────

    def ledger_append(self, root: SkillsRoot | Path, entry: dict) -> dict:
        stored = dict(entry)
        stored.setdefault("id", str(uuid.uuid4()))
        stored.setdefault("ts", now_iso())
        stored.setdefault(
            "actor",
            getattr(
                load_lifecycle_config(SkillsRoot(root)),
                "actor",
                None,
            )
            or DEFAULT_LEDGER_ACTOR,
        )
        stored.setdefault("action", "patch")
        stored.setdefault("skill", "")
        stored.setdefault("before", [])
        stored.setdefault("after", [])
        stored.setdefault("evidence", {})

        blobs = _blob_dir(root)
        blobs.mkdir(parents=True, exist_ok=True)
        for manifest in (stored["before"], stored["after"]):
            for item in manifest:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                digest = item.get("sha256")
                if not isinstance(path, str) or not isinstance(digest, str):
                    continue
                if not _is_valid_sha256(digest):
                    raise SkillsUsageError(
                        f"ledger_append: rejected invalid sha256 digest: {digest!r}"
                    )
                src = Path(root) / path
                dst = blobs / digest
                if dst.exists() or not src.is_file():
                    continue
                if sha256(src.read_bytes()).hexdigest() != digest:
                    continue
                try:
                    shutil.copyfile(src, dst)
                except OSError as exc:
                    logger.warning(
                        "ledger_append: blob store copy failed for %s -> %s: %s",
                        src,
                        dst,
                        exc,
                    )

        target = _ledger_file(root)
        line = json.dumps(stored, sort_keys=True) + "\n"
        try:
            with target.open("a", encoding="utf-8") as handle:
                handle.write(line)
        except OSError as exc:
            logger.warning("ledger_append: failed to append to %s: %s", target, exc)

        return stored

    def ledger_read(
        self,
        root: SkillsRoot | Path,
        limit: int | None = None,
    ) -> tuple[dict, ...]:
        target = _ledger_file(root)
        if not target.is_file():
            return ()

        entries: list[dict] = []
        try:
            with target.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        entry = json.loads(stripped)
                    except ValueError:
                        continue
                    if isinstance(entry, dict):
                        entries.append(entry)
        except OSError as exc:
            logger.warning("ledger_read: error reading %s: %s", target, exc)
            return ()

        if limit is not None:
            if limit <= 0:
                return ()
            entries = entries[-limit:]
        return tuple(entries)

    def ledger_compact(
        self,
        root: SkillsRoot | Path,
        older_than_days: int | None = None,
        keep_recent: int = 0,
    ) -> dict:
        target = _ledger_file(root)
        if not target.is_file():
            return {"entries_before": 0, "entries_after": 0, "blobs_garbage_collected": []}

        days = older_than_days
        if days is None:
            days = DEFAULT_LEDGER_COMPACT_DAYS
        if days < 0:
            raise SkillsUsageError(f"compact days must be non-negative, got {days}")
        if keep_recent < 0:
            raise SkillsUsageError(f"compact keep_recent must be non-negative, got {keep_recent}")

        entries = list(self.ledger_read(root))
        entries_before = len(entries)
        cutoff_index = len(entries) - keep_recent if keep_recent else len(entries)
        kept_candidates = [
            e for e in entries[:cutoff_index] if _is_newer_than(e, days)
        ]
        retained = kept_candidates + entries[cutoff_index:]

        if retained != entries:
            temp_path = target.with_name(f"{target.name}.tmp-{uuid.uuid4().hex}")
            try:
                with temp_path.open("w", encoding="utf-8") as handle:
                    for entry in retained:
                        handle.write(json.dumps(entry, sort_keys=True) + "\n")
                os.replace(temp_path, target)
            except OSError:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise

        blobs_garbage_collected: list[str] = []
        blobs = _blob_dir(root)
        if blobs.is_dir():
            live_blobs: set[str] = set()
            for entry in retained:
                live_blobs.update(manifest_sha256(entry.get("after", [])))
                live_blobs.update(manifest_sha256(entry.get("before", [])))
            for blob_file in blobs.iterdir():
                if blob_file.is_file() and blob_file.name not in live_blobs:
                    blob_file.unlink()
                    blobs_garbage_collected.append(blob_file.name)

        return {
            "entries_before": entries_before,
            "entries_after": len(retained),
            "blobs_garbage_collected": sorted(blobs_garbage_collected),
        }

    def rollback_entry(self, root: SkillsRoot | Path, entry_id: str) -> dict:
        target = _ledger_file(root)
        if not target.is_file():
            raise MutationConflictError("rollback_entry: no ledger file found")

        entries = self.ledger_read(root)
        match: dict | None = None
        for candidate in reversed(entries):
            if candidate.get("id") == entry_id:
                match = candidate
                break

        if match is None:
            raise MutationConflictError(f"rollback_entry: entry not found: {entry_id!r}")

        blobs = _blob_dir(root)
        after_manifest = match.get("after") or []
        for item in after_manifest:
            digest = item.get("sha256")
            if not isinstance(digest, str) or not (blobs / digest).is_file():
                raise MutationConflictError(
                    f"rollback_entry: missing blob for after-state: "
                    f"{BLOBS_DIRNAME}/{digest}"
                )

        restored_files: list[str] = []
        for item in after_manifest:
            rel = item["path"]
            digest = item["sha256"]
            dest = Path(root) / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(blobs / digest, dest)
            restored_files.append(str(dest))

        self.ledger_append(
            root,
            {
                "action": "rollback",
                "skill": match.get("skill", ""),
                "before": after_manifest,
                "after": after_manifest,
                "evidence": {"rollback_target": entry_id},
            },
        )

        return {
            "rolled_back": True,
            "entry_id": entry_id,
            "restored_files": restored_files,
        }
