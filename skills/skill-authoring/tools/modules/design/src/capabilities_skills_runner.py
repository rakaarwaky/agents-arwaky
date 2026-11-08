"""Skill runner capability (AES capabilities layer).

Runs the automatic transitions pass, and flips the pause marker on the
lifecycle config.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from shared.src.design.contract_skills_protocol import (
    ISkillsRunnerProtocol,
)
from shared.src.design.taxonomy_skills_constant import LIFECYCLE_STATES
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.design.taxonomy_skills_vo import load_lifecycle_config
from shared.src.maintenance.utility_lifecycle_support import (
    ACTIVE,
    ARCHIVED,
    DEFAULT_STATE,
    STALE,
    _baseline_record,
    _cron_referenced,
    _normalize,
    _now_iso,
    _parse_iso,
    _read_sidecar,
    _usage_path,
    _with_lock,
    find_skill_dir,
)
from shared.src.maintenance.utility_skills_mutation import atomic_write_json
from shared.src.storage.utility_skill_pack import default_pack_root, iter_skill_mds

__all__ = ["SkillsRunner"]


# ─── Block 1: Module Declaration ───
class SkillsRunner(ISkillsRunnerProtocol):
    """Runner capability: run/pause/resume verbs."""

    # ─── Block 2: Module Contract ───
    def apply_automatic_transitions(self, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        config = load_lifecycle_config(pack_root)
        if getattr(config, "pause", False):
            return {"applied": [], "skipped": [], "state_counts": {}, "paused": True}
        now = datetime.now(UTC)
        stale_cutoff = now - timedelta(days=config.stale_after_days)
        archive_cutoff = now - timedelta(days=config.archive_after_days)
        applied: list[dict] = []
        skipped: list[dict] = []
        counts: dict[str, int] = {state: 0 for state in LIFECYCLE_STATES}

        for skill_md in iter_skill_mds(pack_root):
            name = skill_md.parent.name
            self._seed_record_if_missing(name, pack_root)
            record = _read_sidecar(_usage_path(skill_md.parent))
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
                self._reanchor_clock(name, pack_root)
                counts[STALE] -= 1
                counts[ACTIVE] += 1
                applied.append({"skill": name, "from": STALE, "to": ACTIVE})
            elif anchor <= archive_cutoff:
                self._set_state(name, pack_root, ARCHIVED, archived_at=_now_iso())
                counts[state] -= 1
                counts[ARCHIVED] += 1
                applied.append({"skill": name, "from": state, "to": ARCHIVED})
            elif anchor <= stale_cutoff and state == ACTIVE:
                self._set_state(name, pack_root, STALE)
                counts[ACTIVE] -= 1
                counts[STALE] += 1
                applied.append({"skill": name, "from": ACTIVE, "to": STALE})

        return {"applied": applied, "skipped": skipped, "state_counts": counts}

    def pause(self, root: SkillsRoot) -> dict:
        config = load_lifecycle_config(SkillsRoot(root))
        new_dict = asdict(replace(config, pause=True))
        config_path = Path(root) / ".lifecycle_config.json"
        atomic_write_json(config_path, new_dict)
        return {"paused": True}

    def resume(self, root: SkillsRoot) -> dict:
        config = load_lifecycle_config(SkillsRoot(root))
        new_dict = asdict(replace(config, pause=False))
        config_path = Path(root) / ".lifecycle_config.json"
        atomic_write_json(config_path, new_dict)
        return {"paused": False}

    def _seed_record_if_missing(self, skill: str, pack_root: Path) -> None:
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            return
        path = _usage_path(skill_dir)

        def work() -> None:
            if _read_sidecar(path):
                return
            try:
                atomic_write_json(path, _baseline_record())
            except OSError:
                pass

        _with_lock(path, work)

    def _reanchor_clock(self, skill: str, pack_root: Path) -> None:
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            return
        path = _usage_path(skill_dir)

        def work() -> None:
            record = _read_sidecar(path)
            record = _normalize(record) if record else _baseline_record()
            now = _now_iso()
            record["last_activity_at"] = now
            record["activity_window_start"] = now
            if not record.get("pinned", False):
                record["state"] = DEFAULT_STATE
            try:
                atomic_write_json(path, record)
            except OSError:
                pass

        _with_lock(path, work)

    # ─── Block 3: Module Helpers ───
    def _set_state(
        self,
        skill: str,
        pack_root: Path,
        state: str,
        *,
        archived_at: str | None = None,
    ) -> None:
        skill_dir = find_skill_dir(skill, pack_root)
        if skill_dir is None:
            return
        path = _usage_path(skill_dir)

        def work() -> None:
            record = _read_sidecar(path)
            record["state"] = state
            if archived_at is not None:
                record["archived_at"] = archived_at
            try:
                atomic_write_json(path, record)
            except OSError:
                pass

        _with_lock(path, work)
