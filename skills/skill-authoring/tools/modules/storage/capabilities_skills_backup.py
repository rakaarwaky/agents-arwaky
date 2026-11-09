"""Skill backup capability (AES capabilities layer).

Creates content-addressed snapshots of the pack under
``.lifecycle_backups/`` and prunes old ones.
"""

from __future__ import annotations
from shared.src.design.contract_skills_protocol import (
    ISkillsBackupProtocol,
)


import json
import logging
import shutil
import tarfile
from pathlib import Path

from shared.src.common.taxonomy_common_error import SkillsRootError
from shared.src.design.taxonomy_skills_vo import (
    load_lifecycle_config,
)
from shared.src.maintenance.utility_lifecycle_support import (
    BACKUP_DIRNAME,
    DEFAULT_KEEP,
    MANIFEST_NAME,
    TARBALL_NAME,
    _iter_pack_files,
    _new_snapshot_name,
    _sha256_of,
    _utc_iso_stamp,
)

logger = logging.getLogger(__name__)

__all__ = ["SkillsBackup"]


# ─── Block 1: Module Declaration ──────────────
class SkillsBackup(ISkillsBackupProtocol):
    """Backup capability: snapshot create / prune."""

# ─── Block 2: Module Contract ─────────────
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
                tar.addfile(info, abs_path.open("rb"))
                manifest_files.append(
                    {
                        "path": rel,
                        "sha256": _sha256_of(abs_path),
                        "size": abs_path.stat().st_size,
                    }
                )

        manifest = {"created_utc": snap_dir.name, "files": manifest_files}
        (snap_dir / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
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

    # ─── public root accessors (used by SkillsRollback) ────────

    def resolve_root(self, root: Path) -> Path:
        """Validate and return the pack root, raising ``SkillsRootError``."""
        return self._require_root(root)

    def backup_root(self, skills_root: Path) -> Path:
        """Return (creating if needed) the snapshot directory under *skills_root*."""
        return self._backup_root(skills_root)

    # ─── internals ─────────────────────────────────────────────

    def _require_root(self, root: Path) -> Path:
        skills_root = Path(root)
        if not skills_root.is_dir():
            raise SkillsRootError(f"pack root not found: {skills_root}")
        return skills_root

    def _backup_root(self, skills_root: Path) -> Path:
        d = skills_root / BACKUP_DIRNAME
        d.mkdir(parents=True, exist_ok=True)
        return d

# ─── Block 3: Module Helpers ─────────
    def _keep_count(self, skills_root: Path) -> int:
        config = load_lifecycle_config(skills_root)
        val = getattr(config, "backup_keep", DEFAULT_KEEP)
        return val if isinstance(val, int) and val > 0 else DEFAULT_KEEP