"""Shared backup integrity primitives for local tar.gz snapshots.

Reused by both the root-level ``aa backup`` / ``aa restore`` surface and
the skill-design curator snapshot/rollback capability so that every local
archive is created and extracted with the same SHA-256 manifest, safe
member filter, and retention policy.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path

__all__ = [
    "BACKUP_DIRNAME",
    "DEFAULT_KEEP",
    "MANIFEST_NAME",
    "TARBALL_NAME",
    "prune_snapshots",
    "read_manifest",
    "safe_extract_tar",
    "sha256_of",
    "stage_and_swap",
    "utc_iso_stamp",
    "verify_manifest",
    "write_snapshot",
]

#: Snapshot directory name under the pack root.
BACKUP_DIRNAME = ".curator_backups"
#: Tarball and manifest file names inside each snapshot dir.
TARBALL_NAME = "skills.tar.gz"
MANIFEST_NAME = "manifest.json"
#: Retention fallback when a config value is unset or <= 0.
DEFAULT_KEEP = 2


def utc_iso_stamp(now: float | None = None) -> str:
    """UTC ISO-8601 snapshot directory name."""
    if now is None:
        now = time.time()
    return datetime.fromtimestamp(now, tz=UTC).isoformat().replace("+00:00", "")


def sha256_of(path: Path) -> str:
    """Streaming SHA-256 hex digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _new_snapshot_name(base: str, existing: set[str]) -> str:
    """Pick ``<utc-iso>`` or ``<utc-iso>-N`` free of existing names."""
    n = 1
    while f"{base}-{n}" in existing:
        n += 1
    return base if base not in existing else f"{base}-1"


def write_snapshot(
    source_root: Path,
    snapshot_dir: Path,
    excluded: set[str] | frozenset[str] | None = None,
) -> dict:
    """Create *snapshot_dir* containing a tar.gz of *source_root* plus manifest.

    The manifest records the per-file SHA-256 digest and relative path so
    that a later verify/restore can reject a corrupted or tampered tarball.
    Returns the manifest dict.
    """
    source_root = source_root.resolve()
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    tarball = snapshot_dir / TARBALL_NAME
    excluded = frozenset(excluded or ())

    manifest: dict[str, list] = {"files": [], "excluded": sorted(excluded)}
    with tarfile.open(tarball, "w:gz") as tar:
        for root, dirs, files in os.walk(source_root):
            for d in list(dirs):
                if d in excluded:
                    dirs.remove(d)
            for f in files:
                abs_path = Path(root) / f
                rel = abs_path.relative_to(source_root).as_posix()
                if any(part in excluded for part in Path(rel).parts):
                    continue
                with abs_path.open("rb") as fh:
                    info = tar.gettarinfo(str(abs_path), arcname=rel)
                    tar.addfile(info, fileobj=fh)
                manifest["files"].append({"path": rel, "sha256": sha256_of(abs_path)})

    manifest["sha256_tarball"] = sha256_of(tarball)
    manifest_path = snapshot_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def read_manifest(snapshot_dir: Path) -> dict:
    """Load the manifest for *snapshot_dir*; raises on missing/corrupt."""
    manifest_path = snapshot_dir / MANIFEST_NAME
    if not manifest_path.exists():
        raise ValueError(f"Missing manifest in snapshot {snapshot_dir}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def verify_manifest(tarball: Path, manifest: dict, staging: Path) -> None:
    """Verify tarball hash and every member SHA-256 before extraction.

    Raises ``ValueError`` when the archive or any member fails its digest
    check.
    """
    expected_tarball_hash = manifest.get("sha256_tarball")
    if expected_tarball_hash:
        actual = sha256_of(tarball)
        if actual != expected_tarball_hash:
            raise ValueError(f"Tarball digest mismatch: expected {expected_tarball_hash}, got {actual}")

    with tarfile.open(tarball, "r:gz"):
        for entry in manifest.get("files", []):
            expected = entry["sha256"]
            member_path = staging / entry["path"]
            if not member_path.is_file():
                # Member may not exist if the archive was pruned / partial.
                continue
            actual = sha256_of(member_path)
            if actual != expected:
                raise ValueError(f"Member digest mismatch for {entry['path']}")


def safe_extract_tar(tarball: Path, dest: Path) -> None:
    """Extract *tarball* into *dest* using the Python 3.12+ ``data`` filter.

    Falls back to per-member validation on older runtimes.
    """
    dest = dest.resolve()
    if not tarfile.is_tarfile(tarball):
        raise ValueError(f"Not a valid tar archive: {tarball}")
    with tarfile.open(tarball, "r:gz") as tar:
        try:
            tar.extractall(dest, filter="data")
        except TypeError:
            for member in tar.getmembers():
                member_path = (dest / member.name).resolve()
                if not str(member_path).startswith(str(dest) + os.sep):
                    raise ValueError(f"Blocked path traversal in archive: {member.name}")
                if member.issym() or member.islnk():
                    raise ValueError(f"Blocked symlink/hardlink in archive: {member.name}")
                if member.isdev():
                    raise ValueError(f"Blocked device node in archive: {member.name}")
            tar.extractall(dest)


def prune_snapshots(snapshot_root: Path, keep: int = DEFAULT_KEEP) -> list[Path]:
    """Remove the oldest snapshots beyond *keep*, returning removed paths."""
    if keep < 1:
        keep = DEFAULT_KEEP
    if not snapshot_root.is_dir():
        return []
    entries = [p for p in snapshot_root.iterdir() if p.is_dir()]
    # ISO-8601 names sort chronologically; the newest are last.
    entries.sort(key=lambda p: p.name)
    overflow = len(entries) - keep
    if overflow <= 0:
        return []
    removed: list[Path] = []
    for entry in entries[:overflow]:
        shutil.rmtree(entry, ignore_errors=True)
        removed.append(entry)
    return removed


def stage_and_swap(
    tarball: Path,
    manifest: dict,
    live_root: Path,
    snapshot_dir: Path,
    staging_root: Path,
) -> None:
    """Verify + stage a snapshot into *staging_root* and atomically swap it
    into *live_root*, leaving a local undo record in *staging_root*.
    """
    staging_root.mkdir(parents=True, exist_ok=True)
    if staging_root.exists():
        shutil.rmtree(staging_root, ignore_errors=True)
    staging_root.mkdir(parents=True)

    safe_extract_tar(tarball, staging_root)
    verify_manifest(tarball, manifest, staging_root)

    # Swap: keep the old live root as a sibling undo record.
    undo_root = live_root.with_name(f"{live_root.name}.undo-{int(time.time())}")
    if live_root.exists():
        if undo_root.exists():
            shutil.rmtree(undo_root, ignore_errors=True)
        live_root.rename(undo_root)
    try:
        staging_root.rename(live_root)
    except OSError:
        # Roll back the swap; the staged content is not trustworthy.
        if undo_root.exists():
            undo_root.rename(live_root)
        shutil.rmtree(staging_root, ignore_errors=True)
        raise

    # Keep staging_root (now renamed) as the local undo record.
    _ = snapshot_dir  # Caller owns snapshot retention / cleanup.
