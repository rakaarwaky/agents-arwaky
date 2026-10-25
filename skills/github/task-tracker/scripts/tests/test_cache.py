"""Unit tests for cache.py.

No network, no gh. Uses a real XDG data home under tmp_path via
``XDG_DATA_HOME`` so tests never write into $HOME or the target repo.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Add the task-tracker skill root to sys.path so ``scripts.*`` is importable
# when pytest collects these tests from the repo root.
_SKILL_DIR = Path(__file__).resolve().parent.parent.parent
if str(_SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_DIR))

from scripts import cache

REPO = Path(__file__).resolve().parent / "fixtures" / "sample_repo"
DISCOVERY = REPO / "discovery.json"


def test_check_emits_extended_feature_schema(monkeypatch: Any, tmp_path: Path) -> None:
    # Point XDG_DATA_HOME at a temp dir so we never write $HOME.
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    result = cache.check(REPO, DISCOVERY)
    assert set(result.keys()) == {"root", "features"}
    root_entries = result["root"]
    assert all({"path", "cached"} <= set(e) for e in root_entries)
    feature_entries = result["features"]
    assert any(f["name"] == "widgets" for f in feature_entries)
    widgets = next(f for f in feature_entries if f["name"] == "widgets")
    assert any(d["path"] == "widgets/BACKLOG.md" for d in widgets["docs"])

    # With no cache file written yet, every readable-but-uncached doc
    # reports cached: false.
    assert all(not e["cached"] for e in widgets["docs"])


def test_refresh_writes_cache_under_xdag(monkeypatch: Any, tmp_path: Path) -> None:
    xdg = tmp_path / "xdg"
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg))
    cache.check(REPO, DISCOVERY, refresh=True)
    cpath = cache.cache_path(REPO)
    assert cpath.is_file()
    payload = json.loads(cpath.read_text(encoding="utf-8"))
    assert payload["repo"] == str(REPO.resolve())
    assert isinstance(payload["docs"], dict)

    # Re-read: the cached hash must match the current content hash.
    import hashlib

    roadmap_hash = hashlib.sha256((REPO / "ROADMAP.md").read_bytes()).hexdigest()
    assert payload["docs"]["ROADMAP.md"] == roadmap_hash


def test_corrupt_cache_is_silently_rebuilt(monkeypatch: Any, tmp_path: Path) -> None:
    xdg = tmp_path / "xdg"
    monkeypatch.setenv("XDG_DATA_HOME", str(xdg))
    cpath = cache.cache_path(REPO)
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text("{not json", encoding="utf-8")
    # --check against a corrupt cache: the cache is silently rebuilt in
    # memory (no hard failure), and --refresh persists the fresh hashes.
    cache.check(REPO, DISCOVERY, refresh=True)
    payload = json.loads(cpath.read_text(encoding="utf-8"))
    assert payload["repo"] == str(REPO.resolve())
    assert isinstance(payload["docs"], dict)


def test_repo_hash_is_first_12_hex() -> None:
    h = cache.repo_hash(REPO)
    assert len(h) == 12
    assert all(c in "0123456789abcdef" for c in h)
