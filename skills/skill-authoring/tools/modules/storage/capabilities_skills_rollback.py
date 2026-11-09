"""Skill rollback capability (AES capabilities layer).

Restores the pack tree from a stored snapshot, staging the live tree so
the operation is reversible. The backup capability is ctor-injected; this
module never imports a sibling capability.
"""

from __future__ import annotations
from shared.src.design.contract_skills_protocol import (
    ISkillsRollbackProtocol,
)


import json
import logging
import shutil
import tarfile
from pathlib import Path
from typing import Any

from shared.src.common.taxonomy_common_error import (
    MutationConflictError,
    SkillsUsageError,
)
from shared.src.maintenance.utility_lifecycle_support import (
    BACKUP_DIRNAME,
    MANIFEST_NAME,
    TARBALL_NAME,
    _assert_member_safe,
    tar_data_filter,
)

logger = logging.getLogger(__name__)

__all__ = ["SkillsRollback"]


# ─── Block 1: Module Declaration ──────────────
class SkillsRollback(ISkillsRollbackProtocol):
    """Rollback capability: restore the pack tree from a snapshot."""

    def __init__(self, backup: Any) -> None:
        self._backup = backup

# ─── Block 2: Module Contract ─────────────
    def rollback(self, root: Path, id_: str | None = None) -> dict:
        skills_root = self._backup.resolve_root(root)
        target = self._resolve_snapshot(skills_root, id_)
        target_name = target.name

        self._backup.create_snapshot(skills_root, _prune=False)
        self._backup.prune_old_snapshots(
            skills_root, excluded=frozenset({target_name})
        )

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

    # ─── internals ─────────────────────────────────────────────

    def _resolve_snapshot(self, skills_root: Path, id_: str | None) -> Path:
        backup_root = self._backup.backup_root(skills_root)
        if id_ is None:
            snaps = [p for p in backup_root.iterdir() if p.is_dir()]
            if not snaps:
                raise SkillsUsageError("no snapshots to roll back to")
            return max(snaps, key=lambda p: p.name)
        if "/" in id_ or "\\" in id_:
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

# ─── Block 3: Module Helpers ─────────
    def _read_manifest(self, snap_dir: Path) -> dict:
        manifest_file = snap_dir / MANIFEST_NAME
        if not manifest_file.is_file():
            return {}
        try:
            return json.loads(manifest_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}