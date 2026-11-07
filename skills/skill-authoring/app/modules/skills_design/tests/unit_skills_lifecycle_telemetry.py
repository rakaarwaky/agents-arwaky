"""Unit tests for ``SkillsTelemetry`` (``.usage.json`` sidecar)."""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from shared.src.common.utility_lifecycle_support import DEFAULT_STATE, FIELDS

from skills_design.src.capabilities_skills_telemetry import SkillsTelemetry
from skills_design.tests.fixture_skills import as_root


def _write_sidecar(root: Path, skill: str, payload: object) -> Path:
    skill_dir = root / "cat" / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {skill}\ndescription: x\n---\n", encoding="utf-8"
    )
    path = skill_dir / ".usage.json"
    path.write_text(
        json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload),
        encoding="utf-8",
    )
    return path


def _read_sidecar(root: Path, skill: str) -> dict:
    return json.loads((root / "cat" / skill / ".usage.json").read_text(encoding="utf-8"))


def _skill_dir(root: Path, skill: str) -> Path:
    return root / "cat" / skill


# ─── seed_record_if_missing ──────────────────────────────────────────


def test_seed_missing_writes_full_baseline(tmp_path: Path) -> None:
    """Missing sidecar → baseline with every field populated."""
    root = tmp_path / "skills"
    _skill_dir(root, "alpha").mkdir(parents=True)
    (root / "cat" / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: x\n---\n", encoding="utf-8"
    )
    SkillsTelemetry().seed_record_if_missing("alpha", as_root(root))

    record = _read_sidecar(root, "alpha")
    assert set(record) == set(FIELDS)
    assert record["state"] == DEFAULT_STATE
    assert record["pinned"] is False
    assert record["created_by"] == "agent"
    assert record["views"] == 0
    assert record["uses"] == 0
    assert record["created_at"] == record["first_seen_at"]
    assert record["created_at"] == record["last_activity_at"]
    assert record["created_at"] == record["activity_window_start"]
    assert record["archived_at"] == ""


def test_seed_existing_never_overwrites(tmp_path: Path) -> None:
    """Existing valid record survives a second seed call unchanged."""
    root = tmp_path / "skills"
    custom = {
        "state": "stale",
        "pinned": True,
        "created_by": "agent",
        "created_at": "2026-01-01T00:00:00+00:00",
        "first_seen_at": "2026-01-01T00:00:00+00:00",
        "last_activity_at": "2026-02-01T00:00:00+00:00",
        "archived_at": "",
        "views": 7,
        "uses": 3,
        "activity_window_start": "2026-01-01T00:00:00+00:00",
    }
    _write_sidecar(root, "alpha", custom)
    SkillsTelemetry().seed_record_if_missing("alpha", as_root(root))
    assert _read_sidecar(root, "alpha") == custom


# ─── reanchor_clock ──────────────────────────────────────────────────


def test_reanchor_not_pinned_resets_state_to_active(tmp_path: Path) -> None:
    """Not-pinned stale record → state == active, timestamps anchor to now."""
    root = tmp_path / "skills"
    stale = {
        "state": "stale",
        "pinned": False,
        "created_by": "agent",
        "created_at": "2026-01-01T00:00:00+00:00",
        "first_seen_at": "2026-01-01T00:00:00+00:00",
        "last_activity_at": "2026-01-01T00:00:00+00:00",
        "archived_at": "",
        "views": 0,
        "uses": 0,
        "activity_window_start": "2026-01-01T00:00:00+00:00",
    }
    _write_sidecar(root, "alpha", stale)
    SkillsTelemetry().reanchor_clock("alpha", as_root(root))

    record = _read_sidecar(root, "alpha")
    assert record["state"] == DEFAULT_STATE
    assert record["last_activity_at"] != "2026-01-01T00:00:00+00:00"
    assert record["activity_window_start"] == record["last_activity_at"]


def test_reanchor_pinned_keeps_state_still_anchors(tmp_path: Path) -> None:
    """Pinned record (any state) → state unchanged, last_activity_at anchors."""
    root = tmp_path / "skills"
    pinned = {
        "state": "archived",
        "pinned": True,
        "created_by": "agent",
        "created_at": "2026-01-01T00:00:00+00:00",
        "first_seen_at": "2026-01-01T00:00:00+00:00",
        "last_activity_at": "2026-01-01T00:00:00+00:00",
        "archived_at": "2026-02-01T00:00:00+00:00",
        "views": 0,
        "uses": 0,
        "activity_window_start": "2026-01-01T00:00:00+00:00",
    }
    _write_sidecar(root, "alpha", pinned)
    SkillsTelemetry().reanchor_clock("alpha", as_root(root))

    record = _read_sidecar(root, "alpha")
    assert record["state"] == "archived"  # pinned: state untouched
    assert record["last_activity_at"] != "2026-01-01T00:00:00+00:00"  # still anchors


# ─── curated_report ──────────────────────────────────────────────────


def test_curated_report_empty_pack(tmp_path: Path) -> None:
    """Empty pack → empty list."""
    root = tmp_path / "skills"
    root.mkdir()
    assert SkillsTelemetry().curated_report(as_root(root)) == []


def test_curated_report_mixed_seeds_unsorted_and_sorts(tmp_path: Path) -> None:
    """Mixed seeded/unseeded skills → unseeded seeded, all rows, sorted by name."""
    root = tmp_path / "skills"
    seeded = {
        "state": "stale",
        "pinned": False,
        "created_by": "agent",
        "created_at": "2026-01-01T00:00:00+00:00",
        "first_seen_at": "2026-01-01T00:00:00+00:00",
        "last_activity_at": "2026-01-01T00:00:00+00:00",
        "archived_at": "",
        "views": 1,
        "uses": 2,
        "activity_window_start": "2026-01-01T00:00:00+00:00",
    }
    _write_sidecar(root, "alpha", seeded)
    _write_sidecar(root, "gamma", {})
    for skill in ("beta",):
        _skill_dir(root, skill).mkdir(parents=True)
        (root / "cat" / skill / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: x\n---\n", encoding="utf-8"
        )

    report = SkillsTelemetry().curated_report(as_root(root))
    assert [row["state"] for row in report] == ["stale", "active", "active"]
    assert [row["uses"] for row in report] == [2, 0, 0]


def test_curated_report_fields_match_sidecar(tmp_path: Path) -> None:
    """Report rows are keyed by the .usage.json field names."""
    root = tmp_path / "skills"
    _write_sidecar(root, "alpha", {"state": "active", "pinned": False})
    report = SkillsTelemetry().curated_report(as_root(root))
    assert len(report) == 1
    assert set(report[0]) == set(FIELDS)


# ─── view / use / use_with_timestamp ─────────────────────────────────


def test_view_bumps_counter_and_reanchors(tmp_path: Path) -> None:
    """view: views bumped, clock reanchored, sidecar updated on disk."""
    root = tmp_path / "skills"
    _write_sidecar(root, "alpha", {"views": 2, "uses": 0, "last_activity_at": "old"})
    before = _read_sidecar(root, "alpha")["last_activity_at"]
    SkillsTelemetry().view("alpha", as_root(root))
    after = _read_sidecar(root, "alpha")
    assert after["views"] == 3
    assert after["uses"] == 0
    assert after["last_activity_at"] != before


def test_use_bumps_counter_and_reanchors(tmp_path: Path) -> None:
    """use: uses bumped, clock reanchored, sidecar updated on disk."""
    root = tmp_path / "skills"
    _write_sidecar(root, "alpha", {"views": 0, "uses": 5})
    SkillsTelemetry().use("alpha", as_root(root))
    after = _read_sidecar(root, "alpha")
    assert after["uses"] == 6
    assert after["views"] == 0
    assert after["last_activity_at"] != "2026-01-01T00:00:00+00:00"


def test_use_with_timestamp_bumps_counter_and_reanchors(tmp_path: Path) -> None:
    """use_with_timestamp: uses bumped, clock reanchored, sidecar updated."""
    root = tmp_path / "skills"
    _write_sidecar(root, "alpha", {"uses": 0})
    SkillsTelemetry().use_with_timestamp("alpha", as_root(root))
    after = _read_sidecar(root, "alpha")
    assert after["uses"] == 1
    assert after["last_activity_at"] != ""


# ─── concurrency ─────────────────────────────────────────────────────


def _worker(args: tuple[str, int]) -> int:
    """Hammer seed_record_if_missing + use on the same sidecar; return bumps done."""
    root_str, n = args
    telemetry = SkillsTelemetry()
    for _ in range(n):
        telemetry.seed_record_if_missing("alpha", as_root(Path(root_str)))
        telemetry.use("alpha", as_root(Path(root_str)))
    return n


def test_concurrent_seed_and_use_are_consistent(tmp_path: Path) -> None:
    """N concurrent writers: final record consistent, valid JSON, uses == total bumps."""
    root = tmp_path / "skills"
    _skill_dir(root, "alpha").mkdir(parents=True)
    (root / "cat" / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: x\n---\n", encoding="utf-8"
    )
    writers = 8
    bumps_per_writer = 50
    total = writers * bumps_per_writer
    with ProcessPoolExecutor(max_workers=writers) as pool:
        results = list(
            pool.map(_worker, [(str(root), bumps_per_writer)] * writers)
        )
    assert sum(results) == total

    record = _read_sidecar(root, "alpha")
    assert record["uses"] == total
    assert isinstance(record["uses"], int)
    assert record["state"] == DEFAULT_STATE


# ─── corrupt / malformed sidecar ─────────────────────────────────────


def test_truncated_json_degrades_gracefully(tmp_path: Path) -> None:
    """Truncated (non-JSON) sidecar → best-effort reseed, no raise."""
    root = tmp_path / "skills"
    path = _write_sidecar(root, "alpha", "{not valid json")
    SkillsTelemetry().use("alpha", as_root(root))
    # No exception propagated; file holds valid JSON after reseed.
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["uses"] == 1
    assert set(record) == set(FIELDS)


def test_empty_brace_sidecar_degrades_gracefully(tmp_path: Path) -> None:
    """Empty {} sidecar → best-effort reseed on use, no crash."""
    root = tmp_path / "skills"
    _write_sidecar(root, "alpha", {})
    SkillsTelemetry().use("alpha", as_root(root))
    record = _read_sidecar(root, "alpha")
    assert record["uses"] == 1


def test_wrong_schema_sidecar_degrades_gracefully(tmp_path: Path) -> None:
    """Wrong-schema content → best-effort reseed to a valid baseline record, no raise."""
    root = tmp_path / "skills"
    path = _write_sidecar(root, "alpha", ["not", "a", "dict"])
    SkillsTelemetry().view("alpha", as_root(root))
    SkillsTelemetry().use("alpha", as_root(root))
    SkillsTelemetry().reanchor_clock("alpha", as_root(root))

    # A list payload is not a dict, so _read_sidecar returns {} and the public
    # methods reseed the sidecar to a valid baseline record (never the raw list).
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["views"] == 1
    assert record["uses"] == 1
    assert record["state"] == "active"
    assert set(record) == set(FIELDS)
    assert record["created_at"] == record["first_seen_at"]
    assert record["last_activity_at"] == record["activity_window_start"]


# ─── atomic-write failure path ───────────────────────────────────────


def _boom(path: Path, payload: object) -> None:
    raise OSError("disk full")


def test_atomic_write_failure_degrades_all_methods(tmp_path: Path, monkeypatch) -> None:
    """Monkeypatched atomic_write_json raising → all methods no-op, no propagate."""
    root = tmp_path / "skills"
    _write_sidecar(root, "alpha", {"views": 1, "uses": 2})
    monkeypatch.setattr(
        "skills_design.src.capabilities_skills_telemetry.atomic_write_json",
        _boom,
    )
    telemetry = SkillsTelemetry()
    before = _read_sidecar(root, "alpha")
    telemetry.view("alpha", as_root(root))
    telemetry.use("alpha", as_root(root))
    telemetry.use_with_timestamp("alpha", as_root(root))
    telemetry.seed_record_if_missing("alpha", as_root(root))
    telemetry.reanchor_clock("alpha", as_root(root))
    after = _read_sidecar(root, "alpha")
    assert after == before  # nothing written on failure


# ─── edge cases ──────────────────────────────────────────────────────


def test_zero_and_negative_timestamps_accepted(tmp_path: Path) -> None:
    """Zero/negative timestamps → best-effort, no crash."""
    root = tmp_path / "skills"
    _write_sidecar(
        root,
        "alpha",
        {
            "state": "active",
            "pinned": False,
            "created_by": "agent",
            "created_at": 0,
            "first_seen_at": -1,
            "last_activity_at": -5,
            "archived_at": "",
            "views": 0,
            "uses": 0,
            "activity_window_start": 0,
        },
    )
    SkillsTelemetry().use("alpha", as_root(root))
    record = _read_sidecar(root, "alpha")
    assert record["uses"] == 1


def test_large_int_counters(tmp_path: Path) -> None:
    """Large int counters → bump works, no crash."""
    root = tmp_path / "skills"
    _write_sidecar(root, "alpha", {"views": 2**62, "uses": 2**62})
    SkillsTelemetry().view("alpha", as_root(root))
    assert _read_sidecar(root, "alpha")["views"] == 2**62 + 1


def test_non_writable_directory_no_op(tmp_path: Path, monkeypatch) -> None:
    """Write failure → best-effort no-op, sidecar unchanged on disk."""
    root = tmp_path / "skills"
    _skill_dir(root, "alpha").mkdir(parents=True)
    (root / "cat" / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: x\n---\n", encoding="utf-8"
    )
    path = root / "cat" / "alpha" / ".usage.json"
    path.write_text(
        json.dumps(
            {
                "state": "active",
                "pinned": False,
                "created_by": "agent",
                "created_at": "t0",
                "first_seen_at": "t0",
                "last_activity_at": "t0",
                "archived_at": "",
                "views": 0,
                "uses": 0,
                "activity_window_start": "t0",
            }
        ),
        encoding="utf-8",
    )
    before = json.loads(path.read_text(encoding="utf-8"))

    def _boom(path: Path, payload: object) -> None:
        raise PermissionError("read-only filesystem")

    monkeypatch.setattr(
        "skills_design.src.capabilities_skills_telemetry.atomic_write_json",
        _boom,
    )
    SkillsTelemetry().use("alpha", as_root(root))

    # Sidecar untouched on disk: best-effort no-op degrades gracefully.
    assert json.loads(path.read_text(encoding="utf-8")) == before
