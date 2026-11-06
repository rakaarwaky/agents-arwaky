"""Curator audit-ledger capability (AES capabilities layer).

Append-only JSONL ledger (``.curator_ledger.jsonl``) plus
content-addressed before/after blobs (``.curator_backups/blobs/<sha256>``),
per ``skill-audit-ledger.md``. The ledger is telemetry, not a gate:
``ledger_append`` swallows I/O errors and returns the entry; only
``rollback_entry`` fails closed, when a ``pre-rollback`` safety capture is
missing a blob, via ``MutationConflictError``.

Plain capability class: does NOT inherit ``ISkillsCuratorProtocol`` and
adds no raise-stubs for the protocol's other methods (composition is the
agent's concern, not this file's). The seam types are plain ``dict`` /
``tuple[dict, ...]`` (the design doc data-model table); PR 1's
``LedgerEntry`` dataclass carries the same field names for callers that
want the named VO.

No sibling imports (AES201): the config loader and error types come from
the shared taxonomy layer; the compaction's atomic rewrite is local
(temp file + ``os.replace``) because the shared kernel has no JSONL
atomic writer.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from shared.src.skills_design.taxonomy_skills_curator_config_vo import (
    load_curator_config,
)
from shared.src.skills_design.taxonomy_skills_error import MutationConflictError
from shared.src.skills_design.taxonomy_skills_request import SkillsRoot

__all__ = [
    "BLOBS_DIRNAME",
    "DEFAULT_LEDGER_ACTOR",
    "DEFAULT_LEDGER_COMPACT_DAYS",
    "LEDGER_FILENAME",
    "SkillsCuratorLedger",
    "entry_ts",
    "manifest_sha256",
    "now_iso",
]

#: Ledger file name under the skills pack root (``skill-audit-ledger.md``).
LEDGER_FILENAME = ".curator_ledger.jsonl"
#: Content-addressed blob dir under the pack root.
BLOBS_DIRNAME = "blobs"
#: ``actor`` fallback when ``load_curator_config(root).actor`` is unset
#: (PR 1's ``CuratorConfig`` has no ``actor`` field; its spec default is
#: ``"curator"``).
DEFAULT_LEDGER_ACTOR = "curator"
#: Compact window fallback in days when the config has no
#: ``ledger_compact_days`` knob (PR 1's ``CuratorConfig`` has no such
#: field; wiki default retention).
DEFAULT_LEDGER_COMPACT_DAYS = 90


def now_iso() -> str:
    """Current UTC time as ISO 8601, microseconds precision."""
    return datetime.now(UTC).isoformat(timespec="microseconds")


def entry_ts(entry: dict[str, Any]) -> str:
    """An entry's ``ts`` field, empty string when missing or not a str."""
    value = entry.get("ts")
    return value if isinstance(value, str) and value else ""


def _parse_ts(ts: str) -> float | None:
    """Strict-parse a ledger ``ts`` to epoch seconds; ``None`` when unreadable."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts).timestamp()
    except (ValueError, TypeError):
        return None


def _is_newer_than(ts: str, days: int) -> bool:
    """True when ``ts`` is within the last ``days`` days, or unreadable."""
    parsed = _parse_ts(ts)
    if parsed is None:
        return True  # unreadable timestamps survive compaction (fail-open)
    cutoff = _parse_ts(now_iso()) - days * 86400
    return parsed >= cutoff


def _sha256_of(path: Path) -> str:
    """SHA-256 of a file's bytes (the content-address key)."""
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_sha256(manifest: Any) -> str:
    """Unique ``sha256`` values named by a manifest, in first-seen order."""
    seen: dict[str, None] = {}
    if isinstance(manifest, Iterable) and not isinstance(manifest, (str, bytes)):
        for item in manifest:
            if isinstance(item, dict):
                digest = item.get("sha256")
                if isinstance(digest, str) and digest and digest not in seen:
                    seen[digest] = None
    return list(seen)


def _blob_dir(root: SkillsRoot | None) -> Path:
    return root / ".curator_backups" / BLOBS_DIRNAME  # type: ignore[operator]


def _ledger_file(root: SkillsRoot | None) -> Path:
    return root / LEDGER_FILENAME  # type: ignore[operator]


class SkillsCuratorLedger:
    """Append-only audit ledger with content-addressed blobs.

    ``ledger_append`` / ``ledger_read`` / ``ledger_compact`` /
    ``rollback_entry`` over the pack-root ledger file and blob store.
    """

    def ledger_append(self, root: SkillsRoot, entry: dict) -> dict:
        """Append one entry; return it as stored (id/ts/actor filled in).

        Telemetry, not a gate: a ledger write failure is swallowed
        (logged) and the filled entry is still returned; a blob-copy
        failure leaves the ledger line intact.
        """
        stored = dict(entry)
        stored.setdefault("id", str(uuid.uuid4()))
        stored.setdefault("ts", now_iso())
        stored.setdefault(
            "actor",
            getattr(
                load_curator_config(root),  # type: ignore[arg-type]
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

        blobs = _blob_dir(root)  # type: ignore[arg-type]
        blobs.mkdir(parents=True, exist_ok=True)
        for manifest in (stored["before"], stored["after"]):
            for item in manifest:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                digest = item.get("sha256")
                if not isinstance(path, str) or not isinstance(digest, str):
                    continue
                blob = blobs / digest
                source = Path(path)
                if blob.exists():
                    continue
                if not source.is_file():
                    continue
                if digest != _sha256_of(source):
                    # Manifest digest does not match the file's real bytes:
                    # the safety capture is absent by content, never forged.
                    continue
                try:
                    shutil.copyfile(source, blob)
                except OSError as exc:
                    # Telemetry, not a gate: a torn blob is recoverable
                    # (re-copy on a later append); never fail the ledger.
                    print(
                        f"WARNING: ledger blob copy failed for {path}: {exc}",
                        flush=True,
                    )
        line = json.dumps(stored, sort_keys=True)
        try:
            with _ledger_file(root).open("a", encoding="utf-8") as handle:  # type: ignore[arg-type]
                handle.write(line + "\n")
        except OSError as exc:
            # Telemetry, not a gate: every public write swallows and logs.
            print(f"WARNING: ledger append failed: {exc}", flush=True)
        return stored

    def ledger_read(self, root: SkillsRoot) -> tuple[dict, ...]:
        """Read every valid line, oldest first; drop a torn trailing line.

        A missing ledger is an empty tuple; an interrupted append leaves a
        partial last line, which is recovered by dropping it (never raised).
        """
        file = _ledger_file(root)  # type: ignore[arg-type]
        if not file.is_file():
            return ()
        entries: list[dict] = []
        try:
            lines = file.read_text(encoding="utf-8").splitlines()
        except OSError:
            return ()
        for line in lines:
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(parsed, dict):
                entries.append(parsed)
        return tuple(entries)

    def ledger_compact(self, root: SkillsRoot) -> dict:
        """Trim entries older than the compact window and GC orphan blobs.

        Rewrites the JSONL atomically (temp file + ``os.replace``) so a
        crash mid-compact never leaves a torn file; then removes any blob
        whose sha256 is no longer referenced by a surviving entry's
        ``before``/``after`` manifest.
        """
        config = load_curator_config(root)  # type: ignore[arg-type]
        days = getattr(config, "ledger_compact_days", None) or DEFAULT_LEDGER_COMPACT_DAYS
        entries = self.ledger_read(root)
        surviving = [e for e in entries if _is_newer_than(entry_ts(e), days)]
        referenced: set[str] = set()
        for entry in surviving:
            referenced.update(manifest_sha256(entry.get("before")))
            referenced.update(manifest_sha256(entry.get("after")))

        file = _ledger_file(root)  # type: ignore[arg-type]
        tmp = file.with_name(file.name + ".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            for entry in surviving:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        os.replace(tmp, file)

        gc: list[str] = []
        blobs = _blob_dir(root)  # type: ignore[arg-type]
        if blobs.is_dir():
            for blob in sorted(blobs.iterdir()):
                if blob.is_file() and blob.name not in referenced:
                    try:
                        blob.unlink()
                        gc.append(blob.name)
                    except OSError:
                        gc.append(blob.name + " (unlink failed)")
        return {
            "entries_before": len(entries),
            "entries_after": len(surviving),
            "blobs_garbage_collected": gc,
            "ts": now_iso(),
        }

    def rollback_entry(self, root: SkillsRoot, entry_id: str) -> dict:
        """Verify a ``pre-rollback`` safety capture, then append a ``rollback``.

        Fails closed: if any ``after`` manifest blob of the referenced
        entry is missing under ``.curator_backups/blobs/``, raise
        ``MutationConflictError`` naming the missing blob and touch
        nothing. On success append an ``action="rollback"`` entry whose
        ``evidence["rollback_target"]`` is the pre-rollback id and return
        the restore description; the live-tree restore itself is PR 4's
        ``SkillsCuratorBackup.rollback`` job.
        """
        blobs = _blob_dir(root)  # type: ignore[arg-type]
        target = next(
            (e for e in self.ledger_read(root) if e.get("id") == entry_id), None
        )
        if target is None:
            raise MutationConflictError(
                f"rollback: ledger entry not found: {entry_id}"
            )
        missing = [
            f"{BLOBS_DIRNAME}/{digest}"
            for digest in manifest_sha256(target.get("after"))
            if not (blobs / digest).is_file()
        ]
        if missing:
            raise MutationConflictError(
                "rollback: missing safety-capture blob(s): " + ", ".join(missing)
            )
        restored = [
            item.get("path", "")
            for item in target.get("after", [])
            if isinstance(item, dict)
        ]
        self.ledger_append(
            root,
            {
                "action": "rollback",
                "skill": target.get("skill", ""),
                "evidence": {"rollback_target": entry_id},
            },
        )
        return {"rolled_back": True, "entry_id": entry_id, "restored_files": restored}
