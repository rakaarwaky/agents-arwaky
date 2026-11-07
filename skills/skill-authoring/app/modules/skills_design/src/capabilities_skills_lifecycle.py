"""Skills lifecycle capability (AES capabilities layer).

Facade over the focused lifecycle capability modules. One capability
per domain: telemetry, runner, transitions, prune, purge, pin, lock,
adopt, backup, rollback, and the audit ledger. This class wires the
modules together and re-exports the legacy public names so existing
callers (agent, CLI, archiver, tests) keep working unchanged.

Public API:
    SkillsLifecycle
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skills_design.src.capabilities_skills_adopter import SkillsAdopter
from skills_design.src.capabilities_skills_backup import SkillsBackup
from skills_design.src.capabilities_skills_ledger import SkillsLedger
from skills_design.src.capabilities_skills_locker import SkillsLocker
from skills_design.src.capabilities_skills_piner import SkillsPiner
from skills_design.src.capabilities_skills_prune import SkillsPrune
from skills_design.src.capabilities_skills_purge import SkillsPurge
from skills_design.src.capabilities_skills_restore import SkillsRestore
from skills_design.src.capabilities_skills_runner import SkillsRunner
from skills_design.src.capabilities_skills_telemetry import SkillsTelemetry
from skills_design.src.common_lifecycle_support import (
    BACKUP_DIRNAME,
    BLOBS_DIRNAME,
    DEFAULT_KEEP,
    DEFAULT_LEDGER_ACTOR,
    DEFAULT_LEDGER_COMPACT_DAYS,
    DEFAULT_STATE,
    FIELDS,
    LEDGER_FILENAME,
    MANIFEST_NAME,
    TARBALL_NAME,
    entry_ts,
    manifest_sha256,
    now_iso,
    tar_data_filter,
    _parse_iso,
)

from skills_design.src.capabilities_skills_rollback import SkillsRollback

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
    "_parse_iso",
]


class SkillsLifecycle:
    """Unified skill lifecycle capability (telemetry, transitions, backup, ledger)."""

    def __init__(self) -> None:
        self._telemetry = SkillsTelemetry()
        self._runner = SkillsRunner()
        self._piner = SkillsPiner()
        self._locker = SkillsLocker()
        self._adopter = SkillsAdopter()
        self._prune = SkillsPrune()
        self._purge = SkillsPurge()
        self._backup = SkillsBackup()
        self._rollback = SkillsRollback(self._backup)
        self._ledger = SkillsLedger()
        self._restore = SkillsRestore(reanchor=self._telemetry.reanchor_clock)

    # ─── Telemetry ─────────────────────────────────────────────────────

    def seed_record_if_missing(self, skill: str, root: Any) -> None:
        return self._telemetry.seed_record_if_missing(skill, root)

    def reanchor_clock(self, skill: str, root: Any) -> None:
        return self._telemetry.reanchor_clock(skill, root)

    def curated_report(self, root: Any) -> list[dict]:
        return self._telemetry.curated_report(root)

    def view(self, skill: str, root: Any) -> None:
        return self._telemetry.view(skill, root)

    def use(self, skill: str, root: Any) -> None:
        return self._telemetry.use(skill, root)

    def use_with_timestamp(
        self, skill: str, root: Any, now_iso_val: str | None = None
    ) -> None:
        return self._telemetry.use_with_timestamp(skill, root, now_iso=now_iso_val)

    # ─── Runner ────────────────────────────────────────────────────────

    def apply_automatic_transitions(self, root: Any = None) -> dict:
        return self._runner.apply_automatic_transitions(root)

    # ─── Piner / Locker / Adopter ─────────────────────────────────────

    def pin(self, skill: str, root: Any = None) -> dict:
        return self._piner.pin(skill, root)

    def unpin(self, skill: str, root: Any = None) -> dict:
        return self._piner.unpin(skill, root)

    def lock(self, skill: str, root: Any = None) -> dict:
        return self._locker.lock(skill, root)

    def unlock(self, skill: str, root: Any = None) -> dict:
        return self._locker.unlock(skill, root)

    def adopt(self, skill: str, root: Any = None) -> dict:
        return self._adopter.adopt(skill, root)

    # ─── Transitions ───────────────────────────────────────────────────

    def archive(self, skill: str, root: Any = None) -> dict:
        from skills_design.src.skills_lifecycle_core import archive_skill

        pack_root = Path(root) if root is not None else _default_pack_root()
        return archive_skill(skill, pack_root)

    def restore(self, skill: str, root: Any = None) -> dict:
        pack_root = Path(root) if root is not None else _default_pack_root()
        return self._restore.restore(skill, pack_root)

    def prune(
        self,
        root: Any = None,
        days: int | None = None,
        dry_run: bool = False,
    ) -> dict:
        return self._prune.prune(root, days, dry_run)

    def purge(
        self,
        skill: str | None = None,
        root: Any = None,
        dry_run: bool = False,
    ) -> dict:
        return self._purge.purge(skill, root, dry_run)

    # ─── Backup & rollback ─────────────────────────────────────────────

    def snapshot_rollback(
        self,
        root: Any,
        action: str,
        id_: str | None = None,
    ) -> dict:
        skills_root = Path(root)
        if action == "snapshot":
            snap = self._backup.create_snapshot(skills_root)
            return {"action": "snapshot", "snapshot": snap.name, "snapshot_dir": str(snap)}
        if action == "prune":
            removed = self._backup.prune_old_snapshots(skills_root)
            return {"action": "prune", "removed": [str(p) for p in removed]}
        return {"action": "rollback", **self._rollback.rollback(skills_root, id_)}

    def create_snapshot(self, root: Path, *, _prune: bool = True) -> Path:
        return self._backup.create_snapshot(root, _prune=_prune)

    def prune_old_snapshots(
        self, root: Path, *, excluded: frozenset[str] | None = None
    ) -> list[Path]:
        return self._backup.prune_old_snapshots(root, excluded=excluded)

    def rollback(self, root: Path, id_: str | None = None) -> dict:
        return self._rollback.rollback(root, id_)

    # ─── Audit ledger ──────────────────────────────────────────────────

    def ledger_append(self, root: Any, entry: dict) -> dict:
        return self._ledger.ledger_append(root, entry)

    def ledger_read(self, root: Any, limit: int | None = None) -> tuple[dict, ...]:
        return self._ledger.ledger_read(root, limit)

    def ledger_compact(
        self,
        root: Any,
        older_than_days: int | None = None,
        keep_recent: int = 0,
    ) -> dict:
        return self._ledger.ledger_compact(root, older_than_days, keep_recent)

    def rollback_entry(self, root: Any, entry_id: str) -> dict:
        return self._ledger.rollback_entry(root, entry_id)


def _default_pack_root() -> Path:
    from shared.src.common.utility_skill_pack import default_pack_root

    return default_pack_root()
