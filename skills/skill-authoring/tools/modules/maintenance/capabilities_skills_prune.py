"""Skill prune capability (AES capabilities layer).

Bulk-archives idle skills past a configurable days threshold.
"""

from __future__ import annotations
from shared.src.design.contract_skills_protocol import (
    ISkillsPruneProtocol,
)


from datetime import UTC, datetime, timedelta
from pathlib import Path

from shared.src.storage.utility_skill_pack import default_pack_root, iter_skill_mds
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.design.taxonomy_skills_vo import (
    load_lifecycle_config,
)
from shared.src.maintenance.utility_lifecycle_support import (
    ACTIVE,
    _cron_referenced,
    _parse_iso,
    archive_skill,
    read_record,
)

__all__ = ["SkillsPrune"]


# ─── Block 1: Module Declaration ──────────────
class SkillsPrune(ISkillsPruneProtocol):
    """Prune capability: idle-skill archiving."""

# ─── Block 2: Module Contract ─────────────
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
            record = read_record(skill_dir)
            state = record.get("state", ACTIVE)

            if record.get("pinned") or record.get("locked"):
                kept.append({"skill": name, "state": state, "reason": "pinned-or-locked"})
                continue

            if _cron_referenced(pack_root, name):
                kept.append({"skill": name, "state": state, "reason": "cron-referenced"})
                continue

            ts_str = (
                record.get("last_activity_at")
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
                    archive_skill(name, pack_root)
                pruned.append({"skill": name, "days_idle": effective_days})
            else:
                kept.append({"skill": name, "state": state})

        return {"pruned": pruned, "kept": kept}
# ─── Block 3: Module Helpers ─────────