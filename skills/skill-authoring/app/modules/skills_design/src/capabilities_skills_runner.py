"""Skill runner capability (AES capabilities layer).

Runs the automatic transitions pass, and flips the pause marker on the
lifecycle config.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path

from shared.src.common.utility_skill_pack import default_pack_root, iter_skill_mds
from shared.src.common.utility_skills_mutation import atomic_write_json
from shared.src.skills_design.taxonomy_skills_lifecycle_config_vo import (
    load_lifecycle_config,
)
from shared.src.skills_design.taxonomy_skills_lifecycle_vo import LIFECYCLE_STATES
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot

from skills_design.src.common_lifecycle_support import (
    ACTIVE,
    ARCHIVED,
    STALE,
    _now_iso,
    _parse_iso,
    _read_sidecar,
    _usage_path,
    _with_lock,
)

__all__ = ["SkillsRunner"]


class SkillsRunner:
    """Runner capability: run/pause/resume verbs."""

    def apply_automatic_transitions(self, root: SkillsRoot | None = None) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        config = load_lifecycle_config(pack_root)
        if getattr(config, "pause", False):
            return {"applied": [], "skipped": [], "state_counts": {}, "paused": True}
        now = __import__("datetime").datetime.now(__import__("datetime").UTC)
        from datetime import timedelta

        stale_cutoff = now - timedelta(days=config.stale_after_days)
        archive_cutoff = now - timedelta(days=config.archive_after_days)
        applied: list[dict] = []
        skipped: list[dict] = []
        counts: dict[str, int] = {state: 0 for state in LIFECYCLE_STATES}

        for skill_md in iter_skill_mds(pack_root):
            name = skill_md.parent.name
            record = _read_sidecar(_usage_path(skill_md.parent))
            if not record:
                skipped.append({"skill": name, "reason": "no-record"})
                continue
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
                self._set_state(name, pack_root, ACTIVE)
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

    def _set_state(
        self,
        skill: str,
        pack_root: Path,
        state: str,
        *,
        archived_at: str | None = None,
    ) -> None:
        from skills_design.src.skills_lifecycle_core import find_skill_dir

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
