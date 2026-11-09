"""Skill telemetry capability (AES capabilities layer).

Reads and bumps the per-skill ``.usage.json`` sidecar: seeding the record,
reanchoring the clock, counting views, and emitting the curated
report consumed by the ``status`` / ``usage`` surface verbs.
"""

from __future__ import annotations
from shared.src.design.contract_skills_protocol import (
    ISkillsTelemetryProtocol,
)


from pathlib import Path

from shared.src.storage.utility_skill_pack import iter_skill_mds
from shared.src.maintenance.utility_skills_mutation import atomic_write_json
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.maintenance.utility_lifecycle_support import (
    DEFAULT_STATE,
    _baseline_record,
    _normalize,
    _now_iso,
    _read_sidecar,
    _usage_path,
    _with_lock,
    find_skill_dir,
)

__all__ = ["SkillsTelemetry"]


# ─── Block 1: Module Declaration ──────────────
class SkillsTelemetry(ISkillsTelemetryProtocol):
    """Telemetry capability: sidecar reads, bumps, and the curated report."""

# ─── Block 2: Module Contract ─────────────
    def seed_record_if_missing(self, skill: str, root: SkillsRoot) -> None:
        skills_root = Path(root)
        skill_dir = find_skill_dir(skill, skills_root)
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
        skill_dir = find_skill_dir(skill, skills_root)
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

    def curated_report(self, root: SkillsRoot) -> list[dict]:
        skills_root = Path(root)
        rows: list[tuple[str, dict]] = []
        for skill_md in iter_skill_mds(skills_root):
            skill_dir = skill_md.parent
            self.seed_record_if_missing(skill_dir.name, SkillsRoot(skills_root))
            record = _read_sidecar(_usage_path(skill_dir))
            rows.append(
                (skill_dir.name, _normalize(record) if record else _baseline_record())
            )
        rows.sort(key=lambda item: item[0])
        return [record for _name, record in rows]

    def view(self, skill: str, root: SkillsRoot) -> None:
        self._bump(skill, root, "views")

# ─── Block 3: Module Helpers ─────────
    def _bump(
        self,
        skill: str,
        root: SkillsRoot,
        counter_field: str,
        now_iso: str | None = None,
    ) -> None:
        skills_root = Path(root)
        skill_dir = find_skill_dir(skill, skills_root)
        if skill_dir is None:
            return
        path = _usage_path(skill_dir)

        def work() -> None:
            record = _read_sidecar(path)
            record = _normalize(record) if record else _baseline_record()
            current = record.get(counter_field, 0)
            record[counter_field] = (current if isinstance(current, int) else 0) + 1
            now = now_iso or _now_iso()
            record["last_activity_at"] = now
            record["activity_window_start"] = now
            if not record.get("pinned", False):
                record["state"] = DEFAULT_STATE
            try:
                atomic_write_json(path, record)
            except OSError:
                pass

        _with_lock(path, work)
