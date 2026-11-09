"""Skill purge capability (AES capabilities layer).

Removes archived skills past a TTL, or a single named archived skill.
"""

from __future__ import annotations
from shared.src.design.contract_skills_protocol import (
    ISkillsPurgeProtocol,
)


import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from shared.src.storage.utility_skill_pack import default_pack_root, iter_skill_mds
from shared.src.maintenance.utility_skills_mutation import archive_root
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.design.taxonomy_skills_vo import (
    load_lifecycle_config,
)
from shared.src.maintenance.utility_lifecycle_support import (
    _parse_iso,
    find_skill_dir,
    read_record,
)

__all__ = ["SkillsPurge"]


# ─── Block 1: Module Declaration ──────────────
class SkillsPurge(ISkillsPurgeProtocol):
    """Purge capability: archive-TTL cleanup."""

# ─── Block 2: Module Contract ─────────────
    def purge(
        self,
        skill: str | None = None,
        root: SkillsRoot | None = None,
        dry_run: bool = False,
    ) -> dict:
        pack_root = Path(root) if root is not None else default_pack_root()
        config = load_lifecycle_config(pack_root)

        if skill is not None:
            skill_dir = find_skill_dir(skill, pack_root, in_archive=True)
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
            record = read_record(skill_dir)
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
# ─── Block 3: Module Helpers ─────────