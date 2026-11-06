"""Curator telemetry capability (AES capabilities layer).

Reads and writes the per-skill ``.usage.json`` sidecar (``skill-telemetry.md``)
tracking lifecycle state, activity timestamps, and view/use counters for the
Hermes Agent Curator. Does not inherit ``ISkillsCuratorProtocol``; composition
(owner of the protocol's six methods) is PR 6's concern.

Public API:
    seed_record_if_missing  - baseline record at first sight; never overwrites
    reanchor_clock          - anchor timestamps to now; state -> active unless pinned
    curated_report          - one telemetry row per skill, sorted by name
    view / use / use_with_timestamp  - best-effort counter bumps + reanchor + write

All writes go through the shared-kernel ``atomic_write_json`` (temp-file +
os.replace under an fcntl/msvcrt cross-process lock). Counter bumps hold an
exclusive lock on a stable sidecar lock file across read-modify-write so
concurrent writers never lose updates or tear a record. Counter bumps are
best-effort: I/O failures are swallowed so a caller never crashes on a
read-only sidecar.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows has no fcntl
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX has no msvcrt
    msvcrt = None

from shared.src.common.utility_skill_pack import iter_skill_mds
from shared.src.common.utility_skills_mutation import atomic_write_json
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot

__all__ = ["SkillsCuratorTelemetry"]

#: Field order for the per-skill ``.usage.json`` sidecar (``skill-telemetry.md``).
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
_DEFAULT_TIMESTAMP = ""


def _iso_now() -> str:
    """Current UTC time as an ISO 8601 timestamp."""
    return datetime.now(UTC).isoformat()


def _skill_dirs(root: Path) -> list[Path]:
    """Every skill directory (parent of each SKILL.md), sorted by path."""
    if not root.is_dir():
        return []
    return sorted(p.parent for p in iter_skill_mds(root))


def _usage_path(skill_dir: Path) -> Path:
    return skill_dir / ".usage.json"


def _lock_path(path: Path) -> Path:
    """Stable lock file for *path* (never replaced, so flock serializes across procs)."""
    return path.with_name(path.name + ".lock")


def _read_sidecar(path: Path) -> dict:
    """Best-effort read of the sidecar; ``{}`` on missing or corrupt JSON."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        data = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _baseline_record() -> dict:
    """Fresh baseline telemetry record written on first sight of a skill."""
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


def _normalize(record: dict) -> dict:
    """Return only the known telemetry fields, filled with safe defaults."""
    baseline = _baseline_record()
    baseline.update({k: record.get(k, baseline[k]) for k in FIELDS})
    return baseline


def _lock_file(handle) -> None:
    """Take an exclusive, blocking lock on the open handle."""
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    elif msvcrt is not None:
        handle.flush()
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1 << 31 - 1)


def _unlock_file(handle) -> None:
    """Release the lock on the open handle."""
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    elif msvcrt is not None:
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1 << 31 - 1)
        except OSError:
            pass


def _with_lock(path: Path, fn) -> None:
    """Run *fn* while holding an exclusive lock on *path*'s stable lock file.

    Lock failures degrade gracefully: *fn* still runs (best-effort), so a
    read-only environment never crashes a caller.
    """
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


class SkillsCuratorTelemetry:
    """Reads/writes the per-skill ``.usage.json`` telemetry sidecar."""

    # ─── Block 1: seeding ──────────────────────────────────────────

    def seed_record_if_missing(self, skill: str, root: SkillsRoot) -> None:
        """Write a baseline record for *skill* only when none exists.

        An existing valid record is never overwritten. Missing or corrupt
        sidecars degrade to a best-effort reseed and never raise.
        """
        skills_root = Path(root)
        skill_dir = self._resolve_skill_dir(skill, skills_root)
        if skill_dir is None:
            return
        path = _usage_path(skill_dir)

        def work() -> None:
            record = _read_sidecar(path)
            if record:
                return  # valid existing record: never overwrite
            try:
                atomic_write_json(path, _baseline_record())
            except OSError:
                pass

        _with_lock(path, work)

    # ─── Block 2: clock reanchor ───────────────────────────────────

    def reanchor_clock(self, skill: str, root: SkillsRoot) -> None:
        """Anchor ``last_activity_at`` and ``activity_window_start`` to now.

        Resets ``state`` to ``active`` only when the record is not pinned;
        pinned records retain their current state. Missing sidecars are
        seeded first; I/O failures degrade to a no-op.
        """
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

    # ─── Block 3: report ───────────────────────────────────────────

    def curated_report(self, root: SkillsRoot) -> list[dict]:
        """One telemetry row per skill in the pack, sorted by skill name.

        Missing records are seeded first. Every row is keyed by the
        ``.usage.json`` field names (``FIELDS``).
        """
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

    # ─── Block 4: counter bumps ────────────────────────────────────

    def view(self, skill: str, root: SkillsRoot) -> None:
        """Best-effort bump of the ``views`` counter, then reanchor the clock."""
        self._bump(skill, root, "views")

    def use(self, skill: str, root: SkillsRoot) -> None:
        """Best-effort bump of the ``uses`` counter, then reanchor the clock."""
        self._bump(skill, root, "uses")

    def use_with_timestamp(self, skill: str, root: SkillsRoot) -> None:
        """Best-effort bump of the ``uses`` counter, then reanchor the clock."""
        self._bump(skill, root, "uses")

    # ─── Block 5: private helpers ──────────────────────────────────

    def _resolve_skill_dir(self, skill: str, skills_root: Path) -> Path | None:
        """Resolve ``skill`` to its directory under the pack root, or None."""
        if not skills_root.is_dir():
            return None
        for skill_dir in _skill_dirs(skills_root):
            if skill_dir.name == skill:
                return skill_dir
        return None

    def _bump(self, skill: str, root: SkillsRoot, counter: str) -> None:
        """Seed-if-missing, increment *counter*, reanchor, write atomically."""
        skills_root = Path(root)
        skill_dir = self._resolve_skill_dir(skill, skills_root)
        if skill_dir is None:
            return
        path = _usage_path(skill_dir)

        def work() -> None:
            record = _read_sidecar(path)
            if not record:
                record = _baseline_record()
            else:
                record = _normalize(record)
            try:
                record[counter] = int(record.get(counter, 0)) + 1
            except (TypeError, ValueError):
                record[counter] = 1
            record["last_activity_at"] = _iso_now()
            record["activity_window_start"] = record["last_activity_at"]
            try:
                atomic_write_json(path, record)
            except OSError:
                pass

        _with_lock(path, work)
