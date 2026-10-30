"""Discovery + scan cache: XDG, keyed on sha256(content).

Stdlib only. The cache file lives at
``${XDG_DATA_HOME:-$HOME/.local/share}/task-tracker/<repo-hash>.json``,
**not** in the target repo: SKILL.md's completion criterion "No file
changed outside ``docs/task-tracker-ledger.jsonl``" applies to files in
the *target* repo, and the XDG location matches the project's
XDG-artifact rule and the ``pr-babysit`` precedent.

``--check`` emits a JSON object that **extends** the discovery
``feature_schema`` with per-doc cache metadata: each ``docs`` entry
becomes ``{"path": "...", "cached": true|false}``.  ``--refresh``
rewrites the cache file with the current content hashes and re-emits the
same extended shape.

An unreadable or corrupt cache file is silently rebuilt — the cache is an
optimization, never a correctness requirement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

_CACHE_DIR_NAME = "task-tracker"


def log(msg: str) -> None:
    """Emit an observability line to stderr with the script prefix."""
    print(f"[task-tracker:cache] {msg}", file=sys.stderr)


def xdg_data_home() -> Path:
    """Return ``${XDG_DATA_HOME:-$HOME/.local/share}`` as a Path."""
    env = os.environ.get("XDG_DATA_HOME")
    if env:
        return Path(env)
    return Path(os.environ.get("HOME", "/root")) / ".local" / "share"


def repo_hash(repo_root: Path) -> str:
    """First 12 hex chars of ``sha256(<repo-root absolute path>)``."""
    digest = hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()
    return digest[:12]


def cache_path(repo_root: Path) -> Path:
    """The cache file path for this repo (under the XDG data home)."""
    return xdg_data_home() / _CACHE_DIR_NAME / f"{repo_hash(repo_root)}.json"


def _content_hash(path: Path) -> str | None:
    """sha256 of the file content, or None when unreadable."""
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None
    return digest


def _empty_cache(repo_root: Path) -> dict[str, Any]:
    return {"repo": str(repo_root), "docs": {}}


def _load_cache(path: Path, repo_root: Path) -> dict[str, Any]:
    """Load the cache file; rebuild it silently when unreadable or corrupt.

    The cache shape is ``{"repo": "<abs path>", "docs": {"<doc rel>": "<sha256>"}}``.
    A mismatched repo key means the file is from another repo with a
    colliding 12-hex hash — treat it as corrupt.
    """
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        log(f"cache unreadable or corrupt, rebuilding: {path}")
        return _empty_cache(repo_root)
    if not isinstance(payload, dict) or payload.get("repo") != str(repo_root):
        log(f"cache repo key mismatch, rebuilding: {path}")
        return _empty_cache(repo_root)
    docs = payload.get("docs")
    if not isinstance(docs, dict):
        log(f"cache docs field malformed, rebuilding: {path}")
        return _empty_cache(repo_root)
    typed: dict[str, Any] = payload
    typed["docs"] = {str(k): str(v) for k, v in docs.items()}
    return typed


def _save_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def _feature_schema(discovery: Path) -> dict[str, Any]:
    """The Rhai ``feature_schema`` object (``root`` + ``features``)."""
    payload: object = json.loads(discovery.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        log(f"discovery JSON is not an object: {discovery}")
        sys.exit(1)
    return payload


def check(
    repo_root: Path,
    discovery: Path,
    out: str | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    """Compute the extended feature_schema for this repo.

    Each ``docs`` entry becomes ``{"path": ..., "cached": true|false}``.
    ``cached`` is true when the cache carries a content hash for the doc
    and the doc is readable with that exact hash.  With
    ``refresh=True`` the cache file is rewritten with the current
    content hashes (the ``cached`` flags are all true for readable
    docs, false for unreadable ones).
    """
    cpath = cache_path(repo_root)
    payload = _load_cache(cpath, repo_root)
    cached_docs: dict[str, str] = dict(payload.get("docs", {}))
    doc_state: dict[str, dict[str, Any]] = {}

    def _mark(doc_rel: Any) -> dict[str, Any]:
        key = str(doc_rel)
        doc_path = repo_root / key
        readable = _content_hash(doc_path) if doc_path.is_file() else None
        if refresh:
            if readable is not None:
                cached_docs[key] = readable
                cached_map = True
            else:
                cached_docs.pop(key, None)
                cached_map = False
        else:
            cached_map = readable is not None and cached_docs.get(key) == readable
        entry = {"path": key, "cached": cached_map}
        doc_state[key] = entry
        return entry

    schema = _feature_schema(discovery)
    root: list[Any] = list(schema.get("root", []) or [])
    root_entries = [_mark(doc_rel) for doc_rel in root]

    features_in: list[Any] = list(schema.get("features", []) or [])
    extended_features: list[dict[str, Any]] = []
    for feat in features_in:
        if not isinstance(feat, dict):
            continue
        feat_docs = feat.get("docs", []) or []
        doc_entries = [_mark(doc_rel) for doc_rel in feat_docs]
        extended_features.append(
            {
                "name": str(feat.get("name", "")),
                "dir": str(feat.get("dir", "")),
                "docs": doc_entries,
            }
        )

    if refresh:
        payload["docs"] = cached_docs
        _save_cache(cpath, payload)
        log(f"cache refreshed: {cpath} ({len(cached_docs)} docs)")

    result = {"root": root_entries, "features": extended_features}
    text = json.dumps(result, indent=2)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        print(text)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cache.py")
    parser.add_argument("--repo-root", required=True, help="Absolute path to the AES repo.")
    parser.add_argument("--discovery", required=True, help="Discovery JSON (feature_schema).")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Emit the extended feature_schema.")
    group.add_argument("--refresh", action="store_true", help="Rewrite the cache and emit.")
    parser.add_argument("--out", default=None, help="Write JSON here; default: stdout.")
    args = parser.parse_args(argv)

    if not args.check and not args.refresh:
        args.check = True
    discovery = Path(args.discovery)
    if not discovery.is_file():
        log(f"discovery file not found: {discovery}")
        return 1
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.is_dir():
        log(f"repo root not a directory: {repo_root}")
        return 1
    check(repo_root, discovery, out=args.out, refresh=args.refresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
