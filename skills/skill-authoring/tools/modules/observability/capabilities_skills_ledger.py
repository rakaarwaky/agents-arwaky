"""Skill audit-ledger capability (AES capabilities layer).

Append-only JSONL ledger with content-addressed blob storage.
"""

from __future__ import annotations
from shared.src.design.contract_skills_protocol import (
    ISkillsLedgerProtocol,
)


import json
import logging
import shutil
import uuid
from pathlib import Path

from shared.src.common.taxonomy_common_error import (
    MutationConflictError,
    SkillsUsageError,
)
from shared.src.design.taxonomy_skills_request import SkillsRoot
from shared.src.design.taxonomy_skills_vo import (
    load_lifecycle_config,
)
from shared.src.maintenance.utility_lifecycle_support import (
    BLOBS_DIRNAME,
    DEFAULT_LEDGER_ACTOR,
    DEFAULT_LEDGER_COMPACT_DAYS,
    _blob_dir,
    _is_newer_than,
    _is_valid_sha256,
    _ledger_file,
    manifest_sha256,
    now_iso,
)

logger = logging.getLogger(__name__)

__all__ = ["SkillsLedger"]


# ─── Block 1: Module Declaration ──────────────
class SkillsLedger(ISkillsLedgerProtocol):
    """Ledger capability: append / read / compact / rollback."""

# ─── Block 2: Module Contract ─────────────
    def ledger_append(self, root: SkillsRoot | Path, entry: dict) -> dict:
        stored = dict(entry)
        stored.setdefault("id", str(uuid.uuid4()))
        stored.setdefault("ts", now_iso())
        stored.setdefault(
            "actor",
            getattr(
                load_lifecycle_config(SkillsRoot(root)),
                "actor",
                None,
            )
            or DEFAULT_LEDGER_ACTOR,
        )
        stored.setdefault("action", "patch")
        stored.setdefault("skill", "")
        stored.setdefault("before", [])
        stored.setdefault("after", [])
        stored.setdefault("evidence", {})

        blobs = _blob_dir(root)
        blobs.mkdir(parents=True, exist_ok=True)
        for manifest in (stored["before"], stored["after"]):
            for item in manifest:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                digest = item.get("sha256")
                if not isinstance(path, str) or not isinstance(digest, str):
                    continue
                if not _is_valid_sha256(digest):
                    raise SkillsUsageError(
                        f"ledger_append: rejected invalid sha256 digest: {digest!r}"
                    )
                src = Path(root) / path
                dst = blobs / digest
                if dst.exists() or not src.is_file():
                    continue
                if not self._digest_matches(src, digest):
                    continue
                try:
                    shutil.copyfile(src, dst)
                except OSError as exc:
                    logger.warning(
                        "ledger_append: blob store copy failed for %s -> %s: %s",
                        src,
                        dst,
                        exc,
                    )

        target = _ledger_file(root)
        line = json.dumps(stored, sort_keys=True) + "\n"
        try:
            with target.open("a", encoding="utf-8") as handle:
                handle.write(line)
        except OSError as exc:
            logger.warning("ledger_append: failed to append to %s: %s", target, exc)

        return stored

    def ledger_read(
        self,
        root: SkillsRoot | Path,
        limit: int | None = None,
    ) -> tuple[dict, ...]:
        target = _ledger_file(root)
        if not target.is_file():
            return ()

        entries: list[dict] = []
        try:
            with target.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        entry = json.loads(stripped)
                    except ValueError:
                        continue
                    if isinstance(entry, dict):
                        entries.append(entry)
        except OSError as exc:
            logger.warning("ledger_read: error reading %s: %s", target, exc)
            return ()

        if limit is not None:
            if limit <= 0:
                return ()
            entries = entries[-limit:]
        return tuple(entries)

    def ledger_compact(
        self,
        root: SkillsRoot | Path,
        older_than_days: int | None = None,
        keep_recent: int = 0,
    ) -> dict:
        target = _ledger_file(root)
        if not target.is_file():
            return {"entries_before": 0, "entries_after": 0, "blobs_garbage_collected": []}

        days = older_than_days
        if days is None:
            days = DEFAULT_LEDGER_COMPACT_DAYS
        if days < 0:
            raise SkillsUsageError(f"compact days must be non-negative, got {days}")
        if keep_recent < 0:
            raise SkillsUsageError(
                f"compact keep_recent must be non-negative, got {keep_recent}"
            )

        entries = list(self.ledger_read(root))
        entries_before = len(entries)
        cutoff_index = len(entries) - keep_recent if keep_recent else len(entries)
        kept_candidates = [
            e for e in entries[:cutoff_index] if _is_newer_than(e, days)
        ]
        retained = kept_candidates + entries[cutoff_index:]

        if retained != entries:
            temp_path = target.with_name(f"{target.name}.tmp-{uuid.uuid4().hex}")
            try:
                with temp_path.open("w", encoding="utf-8") as handle:
                    for entry in retained:
                        handle.write(json.dumps(entry, sort_keys=True) + "\n")
                import os

                os.replace(temp_path, target)
            except OSError:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise

        blobs_garbage_collected: list[str] = []
        blobs = _blob_dir(root)
        if blobs.is_dir():
            live_blobs: set[str] = set()
            for entry in retained:
                live_blobs.update(manifest_sha256(entry.get("after", [])))
                live_blobs.update(manifest_sha256(entry.get("before", [])))
            for blob_file in blobs.iterdir():
                if blob_file.is_file() and blob_file.name not in live_blobs:
                    blob_file.unlink()
                    blobs_garbage_collected.append(blob_file.name)

        return {
            "entries_before": entries_before,
            "entries_after": len(retained),
            "blobs_garbage_collected": sorted(blobs_garbage_collected),
        }

    def rollback_entry(self, root: SkillsRoot | Path, entry_id: str) -> dict:
        target = _ledger_file(root)
        if not target.is_file():
            raise MutationConflictError("rollback_entry: no ledger file found")

        entries = self.ledger_read(root)
        match: dict | None = None
        for candidate in reversed(entries):
            if candidate.get("id") == entry_id:
                match = candidate
                break

        if match is None:
            raise MutationConflictError(
                f"rollback_entry: entry not found: {entry_id!r}"
            )

        blobs = _blob_dir(root)
        after_manifest = match.get("after") or []
        for item in after_manifest:
            digest = item.get("sha256")
            if not isinstance(digest, str) or not (blobs / digest).is_file():
                raise MutationConflictError(
                    f"rollback_entry: missing blob for after-state: "
                    f"{BLOBS_DIRNAME}/{digest}"
                )

        restored_files: list[str] = []
        for item in after_manifest:
            rel = item["path"]
            digest = item["sha256"]
            dest = Path(root) / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(blobs / digest, dest)
            restored_files.append(str(dest))

        self.ledger_append(
            root,
            {
                "action": "rollback",
                "skill": match.get("skill", ""),
                "before": after_manifest,
                "after": after_manifest,
                "evidence": {"rollback_target": entry_id},
            },
        )

        return {
            "rolled_back": True,
            "entry_id": entry_id,
            "restored_files": restored_files,
        }

    @staticmethod
# ─── Block 3: Module Helpers ─────────
    def _digest_matches(src: Path, digest: str) -> bool:
        from hashlib import sha256 as _sha256

        try:
            return _sha256(src.read_bytes()).hexdigest() == digest
        except OSError:
            return False