"""Curator lifecycle capability (AES capabilities layer).

Moves each curator-managed skill through ``active -> stale -> archived``
(``curator-lifecycle.md``). Plain capability class; does NOT implement
``ISkillsCuratorProtocol`` -- PR 6 owns composition. Sidecar I/O is
shared with the PR 2 ``SkillsCuratorTelemetry`` capability (baseline
seeding, clock reanchors, report rows); state mutations are written
atomically through the shared-kernel ``atomic_write_json``. Audit-ledger
recording of applied transitions is PR 5/6's job, not written here.

Public API:
    apply_automatic_transitions - deterministic stale/archive moves per pass
    archive / restore           - manual CURATOR_ARCHIVE / CURATOR_RESTORE ops
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from shared.src.common.utility_skill_pack import default_pack_root, iter_skill_mds
from shared.src.common.utility_skills_mutation import (
    archive_root,
    assert_within_root,
    atomic_write_json,
)
from shared.src.skills_design.taxonomy_skills_constant import ARCHIVE_DIRNAME
from shared.src.skills_design.taxonomy_skills_curator_config_vo import (
    load_curator_config,
)
from shared.src.skills_design.taxonomy_skills_curator_vo import LIFECYCLE_STATES
from shared.src.skills_design.taxonomy_skills_error import (
    MutationConflictError,
    SkillNotFoundError,
)
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot

from skills_design.src.capabilities_skills_curator_telemetry import (
    SkillsCuratorTelemetry,
)

__all__ = ["SkillsCuratorLifecycle"]

ACTIVE = LIFECYCLE_STATES[0]
STALE = LIFECYCLE_STATES[1]
ARCHIVED = LIFECYCLE_STATES[2]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _cron_referenced(pack_root: Path, skill_name: str) -> bool:
    """True when a cron job under the pack names ``skill_name``.

    The wiki prescribes cron references only as fields on cron jobs
    (``curator-snapshot-rollback.md`` reconciles cron ``skills`` /
    ``skill`` fields) with no per-skill marker, so the concrete check
    is the pack's cron jobs file (``<pack_root>/.cron/jobs.json``): a
    skill is cron-referenced when any job's ``skills`` / ``skill``
    field names it.
    """
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


class SkillsCuratorLifecycle:
    """Automatic + manual lifecycle moves over the ``.usage.json`` sidecar."""

    def apply_automatic_transitions(self, root: SkillsRoot | None = None) -> dict:
        """One curator pass: apply the deterministic stale/archive moves.

        Seeds a baseline sidecar on first sight (clock starts at first
        sight, not epoch), skips pinned / locked / cron-referenced
        skills, moves ``active -> stale`` past ``stale_after_days``,
        reactivates ``stale -> active`` when the activity window is
        fresh, and moves ``stale -> archived`` past
        ``archive_after_days``. Invariant: a never-used skill younger
        than ``stale_after_days`` stays active no matter what.

        Returns ``{"applied": [...], "skipped": [...], "state_counts": {...}}``;
        each applied entry is ``{"skill": name, "from": ..., "to": ...}``
        and each skipped entry ``{"skill": name, "reason": ...}``.
        """
        pack_root = root if root is not None else default_pack_root()
        config = load_curator_config(pack_root)
        telemetry = SkillsCuratorTelemetry()
        now = datetime.now(UTC)
        stale_cutoff = now - timedelta(days=config.stale_after_days)
        archive_cutoff = now - timedelta(days=config.archive_after_days)
        cron_cache: dict[str, bool] = {}

        applied: list[dict] = []
        skipped: list[dict] = []
        counts: dict[str, int] = {state: 0 for state in LIFECYCLE_STATES}

        for skill_md in iter_skill_mds(pack_root):
            name = skill_md.parent.name
            telemetry.seed_record_if_missing(name, pack_root)
            record = self._read_record(skill_md.parent)
            state = record.get("state", ACTIVE)
            if state not in LIFECYCLE_STATES:
                state = ACTIVE
            counts[state] += 1

            if record.get("pinned") or record.get("locked"):
                skipped.append(
                    {
                        "skill": name,
                        "reason": "pinned" if record.get("pinned") else "locked",
                    }
                )
                continue
            if name not in cron_cache:
                cron_cache[name] = _cron_referenced(pack_root, name)
            if cron_cache[name]:
                skipped.append({"skill": name, "reason": "cron"})
                continue

            anchor = _parse_iso(record.get("last_activity_at"))
            if anchor is None:
                skipped.append({"skill": name, "reason": "no-anchor"})
                continue

            # Invariant: never archive a never-used young skill.
            if record.get("uses", 0) == 0:
                created = _parse_iso(record.get("created_at"))
                if created is not None and created > stale_cutoff:
                    skipped.append({"skill": name, "reason": "young-unused"})
                    continue

            window_start = _parse_iso(record.get("activity_window_start"))
            if state == STALE and window_start is not None and window_start > stale_cutoff:
                # Activity resumed after the anchor: reactivate + reanchor.
                telemetry.reanchor_clock(name, pack_root)
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
        """Manual CURATOR_ARCHIVE: two-step one-transaction move to ``_archive/``.

        Step 1 updates the sidecar (``state="archived"`` +
        ``archived_at``); step 2 moves the directory to
        ``_archive/<category>/<skill>/``. If step 2 fails, step 1 is
        rolled back (the directory moves back, the prior ``state`` is
        restored) and ``MutationConflictError`` is raised. A second
        archive on an already-archived skill is a no-op.
        """
        pack_root = root if root is not None else default_pack_root()
        skill_dir = self._find_skill_dir(skill, pack_root, in_archive=False)
        if skill_dir is None:
            # Not in the active pack: check the archive tree for a no-op.
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
        now_iso = _now_iso()

        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            # Second-step precondition violated: the archive slot is
            # already occupied -- step 1 has not run, nothing to roll
            # back, report the conflict.
            raise MutationConflictError(
                f"Archive slot already exists: {destination}"
            )
        moved = False
        record["state"] = ARCHIVED
        record["archived_at"] = now_iso
        self._write_record(skill_dir, record)
        try:
            skill_dir.replace(destination)
            moved = True
        except OSError:
            # Roll back the two-step transaction: if the directory was
            # already moved, move it back; restore the prior sidecar
            # state. A pre-existing occupied archive slot is left as-is.
            if moved:
                destination.replace(skill_dir)
            record["state"] = prior_state
            record.pop("archived_at", None)
            self._write_record(skill_dir, record)
            raise MutationConflictError(
                f"Archive of {skill} failed mid-transaction; rolled back."
            ) from None

        return {"skill": skill, "archived": True, "archived_at": now_iso}

    def restore(self, skill: str, root: SkillsRoot | None = None) -> dict:
        """Manual CURATOR_RESTORE: two-step one-transaction move back.

        Step 1 updates the sidecar (``state="active"``, clears
        ``archived_at``); step 2 moves the directory from
        ``_archive/<category>/<skill>/`` back to its origin. A failed
        step 2 rolls back step 1 and raises
        ``MutationConflictError``. A successful restore reanchors the
        activity clock via ``SkillsCuratorTelemetry.reanchor_clock``.
        """
        pack_root = root if root is not None else default_pack_root()
        archived_dir = self._find_skill_dir(skill, pack_root, in_archive=True)
        if archived_dir is None:
            if self._find_skill_dir(skill, pack_root, in_archive=False) is None:
                raise SkillNotFoundError(f"No skill directory found for: {skill}")
            # Not in the archive tree: nothing to restore.
            return {"skill": skill, "restored": False, "reason": "not-archived"}

        category = archived_dir.parent.name
        origin = pack_root / category / skill
        assert_within_root(origin, pack_root)
        record = self._read_record(archived_dir)
        prior_state = record.get("state", ARCHIVED)
        prior_archived_at = record.get("archived_at")

        origin.parent.mkdir(parents=True, exist_ok=True)
        if origin.exists():
            # Second-step precondition violated: the origin slot is
            # already occupied -- step 1 has not run, nothing to roll
            # back, report the conflict.
            raise MutationConflictError(
                f"Restore slot already exists: {origin}"
            )
        moved = False
        record["state"] = ACTIVE
        record.pop("archived_at", None)
        record["activity_window_start"] = _now_iso()
        record["last_activity_at"] = _now_iso()
        self._write_record(archived_dir, record)
        try:
            archived_dir.replace(origin)
            moved = True
        except OSError:
            # Roll back the two-step transaction: if the directory was
            # already moved, move it back; restore the prior sidecar
            # state. A pre-existing occupied origin slot is left as-is.
            if moved:
                origin.replace(archived_dir)
            record["state"] = prior_state
            if prior_archived_at is not None:
                record["archived_at"] = prior_archived_at
            self._write_record(archived_dir, record)
            raise MutationConflictError(
                f"Restore of {skill} failed mid-transaction; rolled back."
            ) from None

        telemetry = SkillsCuratorTelemetry()
        telemetry.reanchor_clock(skill, pack_root)
        return {"skill": skill, "restored": True, "state": ACTIVE}

    def _find_skill_dir(self, skill: str, pack_root: Path, in_archive: bool) -> Path | None:
        """Find *skill*'s directory in the active pack or the archive tree.

        ``in_archive=False`` walks the active pack; ``in_archive=True``
        walks ``_archive/<category>/<skill>/``. A skill present in both
        (a mid-transaction state) is distinguishable by location.
        """
        skills_root = Path(pack_root)
        if in_archive:
            archive = skills_root / ARCHIVE_DIRNAME
            if archive.is_dir():
                for entry in sorted(archive.iterdir()):
                    candidate = entry / skill
                    if candidate.is_dir() and (
                        (candidate / "SKILL.md").is_file()
                        or (candidate / "SKILL.md.archived").is_file()
                    ):
                        return candidate
            return None
        for skill_md in iter_skill_mds(skills_root):
            if skill_md.parent.name == skill:
                return skill_md.parent
        return None

    def _read_record(self, skill_dir: Path) -> dict:
        """Read the sidecar record for *skill_dir*; empty when missing/corrupt."""
        path = skill_dir / ".usage.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write_record(self, skill_dir: Path, record: dict) -> None:
        """Atomically write *record* to *skill_dir*'s sidecar."""
        atomic_write_json(skill_dir / ".usage.json", record)

