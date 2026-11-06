"""Curator backup capability (AES capabilities layer).

Snapshot + rollback of the skill pack (Hermes curator parity,
``curator-snapshot-rollback.md`` steps 1-6): a snapshot is a tar.gz of the
pack root under ``.curator_backups/<utc-iso>/`` with a ``manifest.json``;
a rollback first snapshots the live tree (undoable), stages it into a
sibling staging dir, extracts the target tarball after a per-member
path-traversal pre-check, and keeps the staging dir as the local undo
record.

Plain capability class: does NOT inherit ``ISkillsCuratorProtocol`` and
adds no raise-stubs for the protocol's other methods (composition is the
agent's concern, not this file's).

No I/O beyond the snapshot/rollback operations; config comes from
``load_curator_config`` (``CuratorConfig.backup_keep`` is the single
effective keep-knob, with a ``DEFAULT_KEEP`` fallback).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shared.src.skills_design.taxonomy_skills_curator_config_vo import (
    CuratorConfig,
    load_curator_config,
)
from shared.src.skills_design.taxonomy_skills_error import (
    MutationConflictError,
    SkillsRootError,
    SkillsUsageError,
)
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot

__all__ = [
    "DEFAULT_KEEP",
    "SkillsCuratorBackup",
    "tar_data_filter",
]

logger = logging.getLogger(__name__)

#: Retention fallback when ``CuratorConfig.backup_keep`` is unset or <= 0.
DEFAULT_KEEP = 2

#: Snapshot dir name under the pack root (``curator-snapshot-rollback.md``).
BACKUP_DIRNAME = ".curator_backups"
#: Tarball and manifest file names inside each snapshot dir.
TARBALL_NAME = "skills.tar.gz"
MANIFEST_NAME = "manifest.json"

#: Exclusion set from ``curator-snapshot-rollback.md`` ("Excluded" table),
#: matched against top-level names and any path component.
EXCLUDED_PATHS: frozenset[str] = frozenset(
    {
        ".curator_backups",
        ".hub",
        ".locks",
        ".git",
        ".archive",
        ".curator_ledger.jsonl",
        "venv",
        "node_modules",
    }
)
#: Cache markers: "caches (any depth)" per the wiki table.
_CACHE_MARKERS: frozenset[str] = frozenset({"__pycache__"})


def _is_cache_dir(name: str) -> bool:
    """Whether a directory name is a cache (any depth, per the wiki)."""
    return name == "__pycache__" or "cache" in name.lower()


def _is_excluded(rel: str) -> bool:
    """Whether ``rel`` (a relative path or single component) is excluded."""
    parts = Path(rel).parts
    for part in parts:
        if part in EXCLUDED_PATHS:
            return True
        if _is_cache_dir(part):
            return True
    return False


def _utc_iso_stamp(now: float | None = None) -> str:
    """UTC ISO-8601 snapshot dir name (``-N`` suffixes handled by caller)."""
    if now is None:
        now = time.time()
    base = datetime.fromtimestamp(now, tz=UTC).isoformat().replace("+00:00", "")
    return base


def _new_snapshot_name(base: str, existing: set[str]) -> str:
    """Pick ``<utc-iso>`` or ``<utc-iso>-N`` free of the existing names."""
    n = 1
    while f"{base}-{n}" in existing:
        n += 1
    return base if base not in existing else f"{base}-{n}"


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_pack_files(root: Path) -> list[tuple[str, Path]]:
    """(relative-path, absolute-path) rows for every non-excluded file."""
    rows: list[tuple[str, Path]] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        kept: list[str] = []
        for d in sorted(dirnames):
            if _is_excluded(d) or _is_cache_dir(d):
                continue
            kept.append(d)
        dirnames[:] = kept
        for name in sorted(filenames):
            if _is_excluded(name) or _is_cache_dir(name):
                continue
            abs_path = Path(dirpath) / name
            rel = abs_path.relative_to(root).as_posix()
            if _is_excluded(rel):
                continue
            rows.append((rel, abs_path))
    return rows


def _assert_member_safe(member: tarfile.TarInfo, target_root: Path) -> None:
    """Per-member pre-extraction check: no ``..``, no absolute, safe links.

    The wiki's ``filter="data"`` alone is necessary but silent; this
    explicit rejection is what the rollback test suite locks.
    """
    name = member.name.lstrip("/")
    if os.path.isabs(member.name):
        raise SkillsUsageError(f"unsafe tarball member (absolute path): {member.name}")
    parts = Path(name).parts
    if ".." in parts:
        raise SkillsUsageError(f"unsafe tarball member (path traversal): {member.name}")
    target = target_root / Path(*parts)
    try:
        target.resolve().relative_to(target_root.resolve())
    except ValueError as exc:
        raise SkillsUsageError(f"unsafe tarball member escapes the pack root: {member.name}") from exc
    if member.issym() or member.islnk():
        link_target = member.linkname
        if os.path.isabs(link_target) or ".." in Path(link_target.lstrip("/")).parts:
            raise SkillsUsageError(f"unsafe tarball link target: {link_target}")
        link_path = target / link_target
        try:
            link_path.resolve().relative_to(target_root.resolve())
        except ValueError as exc:
            raise SkillsUsageError(f"unsafe tarball link target: {link_target}") from exc


def tar_data_filter(member: tarfile.TarInfo, dest_path: str) -> tarfile.TarInfo:
    """Per-member filter: the lib's ``data`` rules plus an explicit pre-check.

    ``extractall`` invokes this as ``filter(member, dest_path)`` with no
    archive, so it cannot wrap ``tarfile.data_filter``; the checks below
    mirror ``tarfile.data_filter`` (absolute paths, ``..`` components,
    unsafe link targets) and then apply this capability's explicit
    per-member rejection so a refusal is testable.
    """
    _assert_member_safe(member, Path(dest_path))
    return member


class SkillsCuratorBackup:
    """Snapshot + rollback of the skill pack (``curator-snapshot-rollback.md``)."""

    def snapshot_rollback(
        self,
        root: SkillsRoot,
        action: str,
        id_: str | None = None,
    ) -> dict:
        """Dispatch ``action`` to the snapshot / prune / rollback verbs."""
        if action not in {"snapshot", "prune", "rollback"}:
            raise SkillsUsageError(f"unknown snapshot_rollback action: {action}")
        skills_root = Path(root)
        if action == "snapshot":
            snap = self.create_snapshot(skills_root)
            return {"action": "snapshot", "snapshot": snap.name, "snapshot_dir": str(snap)}
        if action == "prune":
            removed = self.prune_old_snapshots(skills_root)
            return {"action": "prune", "removed": [str(p) for p in removed]}
        return {"action": "rollback", **self.rollback(skills_root, id_)}

    def create_snapshot(self, root: Path, *, _prune: bool = True) -> Path:
        """Tar.gz the pack root into ``.curator_backups/<utc-iso>/``.

        Same-second re-takes get a ``-N`` uniqueness suffix so a
        rollback's safety snapshot never clobbers the target snapshot.
        After each take, prunes to the configured keep count.
        """
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
                if abs_path.is_dir():
                    tar.addfile(info)
                else:
                    tar.addfile(info, abs_path.open("rb"))
                manifest_files.append(
                    {"path": rel, "sha256": _sha256_of(abs_path), "size": abs_path.stat().st_size}
                )
        manifest = {"created_utc": snap_dir.name, "files": manifest_files}
        (snap_dir / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if _prune:
            self.prune_old_snapshots(skills_root)
        return snap_dir

    def prune_old_snapshots(
        self, root: Path, *, excluded: frozenset[str] | None = None
    ) -> list[Path]:
        """Keep the newest ``CuratorConfig.backup_keep`` snapshot dirs.

        Removes the excess newest-first. ``excluded`` names (e.g. the
        rollback target dir) are never pruned. Returns the removed dirs.
        """
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

    def rollback(self, root: Path, id_: str | None = None) -> dict:
        """Undoable restore from a snapshot (wiki steps 1-6).

        1. Safety snapshot of the live tree first (its prune excludes the
           target dir, so the keep boundary never evicts the target).
        2. Stage the live tree into ``.rollback-staging-<id>/``.
        3. Extract the target tarball after a per-member pre-check,
           ``filter="data"``; on failure: unstage + unrestored record +
           ``MutationConflictError``.
        4. On extract failure: remove the manifest's leaked entries from the
           live tree, un-stage, keep the staging dir as
           ``.rollback-unrestored-<id>``, raise ``MutationConflictError``.
        5. Carry excluded subtrees back from the staged tree.
        6. Staging dir stays on disk as the local undo record (success path).
        """
        skills_root = self._require_root(root)
        target = self._resolve_snapshot(skills_root, id_)
        target_name = target.name

        # Step 1: safety snapshot (prune must not evict the target).
        self.create_snapshot(skills_root, _prune=False)
        self.prune_old_snapshots(skills_root, excluded=frozenset({target_name}))

        staging = skills_root / f".rollback-staging-{target_name}"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()
        # Step 2: stage every top-level live entry except the backup root.
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
            # Un-stage: move entries back, skipping names the live tree has.
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

        # Step 4: carry excluded subtrees back from the staged live tree.
        for entry in sorted(staging.iterdir()):
            if (skills_root / entry.name).exists():
                continue
            shutil.move(str(entry), str(skills_root / entry.name))

        # Step 5: staging dir stays on disk as the undo record.
        return {
            "snapshot": target_name,
            "staging": str(staging),
            "restored": True,
        }

    # ─── internal helpers ──────────────────────────────────

    @staticmethod
    def _require_root(root: Path) -> Path:
        skills_root = Path(root)
        if not skills_root.is_dir():
            raise SkillsRootError(f"skills root is missing or not a directory: {skills_root}")
        return skills_root

    @staticmethod
    def _backup_root(skills_root: Path) -> Path:
        backup_root = skills_root / BACKUP_DIRNAME
        backup_root.mkdir(parents=True, exist_ok=True)
        return backup_root

    @staticmethod
    def _keep_count(skills_root: Path) -> int:
        config: CuratorConfig = load_curator_config(skills_root)
        keep = config.backup_keep
        return keep if isinstance(keep, int) and keep > 0 else DEFAULT_KEEP

    def _resolve_snapshot(self, skills_root: Path, id_: str | None) -> Path:
        backup_root = self._backup_root(skills_root)
        if id_ is None:
            snaps = [p for p in backup_root.iterdir() if p.is_dir()]
            if not snaps:
                raise SkillsUsageError("no snapshots to roll back to")
            return max(snaps, key=lambda p: p.name)
        if "/" in id_ or os.sep in id_:
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

    @staticmethod
    def _read_manifest(snap_dir: Path) -> dict:
        manifest_path = snap_dir / MANIFEST_NAME
        try:
            data: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MutationConflictError(f"snapshot manifest unreadable: {manifest_path}") from exc
        if not isinstance(data, dict):
            raise MutationConflictError(f"snapshot manifest malformed: {manifest_path}")
        return data

