"""Unit tests for ``capabilities_skills_tracker.SkillsTracker``.

Builds a fake ``GROK_HOME`` with a ``sessions/`` tree under ``tmp_path`` and
exercises the tracker capability in-process (no subprocess, no real GROK_HOME).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from modules.shared.src.skills.contract_skills_protocol import ITrackerProtocol
from modules.shared.src.skills.taxonomy_skills_authoring_vo import UsageReport
from modules.shared.src.skills.taxonomy_skills_vo import (
    ScanResult,
    SkillUsageItem,
    TraceSessionRecord,
)
from modules.skills.src.capabilities_skills_tracker import (
    TURN_CAP,
    SkillsTracker,
    redact,
)


def _write_session(grok_home: Path, enc_cwd: str, sid: str, summary: dict, turns: list[str]) -> Path:
    sess_dir = grok_home / "sessions" / enc_cwd / sid
    sess_dir.mkdir(parents=True)
    (sess_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    lines = []
    for t in turns:
        lines.append(json.dumps({"type": "user", "content": f"<user_query>{t}</user_query>", "synthetic_reason": None}))
    (sess_dir / "chat_history.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sess_dir


def _grok_home(tmp_path: Path) -> Path:
    return tmp_path / "grok"


def _make_tracker() -> SkillsTracker:
    return SkillsTracker()


# A cwd outside the OS temp dirs so the default temp-cwd exclusion does not
# drop the fixture sessions (tmp_path itself is under /tmp).
_PROJ_CWD = "/home/raka/proj"


# ---------------------------------------------------------------- protocol conformance


def test_tracker_implements_protocol() -> None:
    """SkillsTracker satisfies the ITrackerProtocol contract."""
    assert isinstance(_make_tracker(), ITrackerProtocol)


def test_trace_session_record_is_frozen() -> None:
    """TraceSessionRecord is an immutable value object."""
    record = TraceSessionRecord(id="s1", index=0, cwd="/w")
    with pytest.raises(AttributeError):
        record.id = "s2"  # type: ignore[misc]


# ---------------------------------------------------------------- redaction (security-critical)


def test_redact_preserves_non_credentials() -> None:
    """Ordinary package names and 40-hex git SHAs are not redacted (per the
    retired collector's comment on SECRET_RES)."""
    assert "npm-package-for-widgets" in redact("use npm-package-for-widgets")
    sha40 = "a" * 40  # a git SHA is 40 hex chars; SECRET_RES needs 64+
    assert sha40 in redact(sha40)


def test_secret_res_redacts_sk_key() -> None:
    """sk-… keys are redacted (SECRET_RES entry 0)."""
    out = redact("key sk-abc123def456ghi789")
    assert "…[redacted]" in out
    assert "sk-abc123def456ghi789" not in out


def test_secret_res_redacts_aws_key() -> None:
    """AKIA… AWS keys are redacted (SECRET_RES entry 1)."""
    out = redact("key ASIAFAKE1234567890AB")
    assert "…[redacted]" in out


def test_secret_res_redacts_jwt() -> None:
    """JWT-style three-segment tokens are redacted (SECRET_RES entry 3)."""
    long_jwt = "a" * 20 + "." + "b" * 20 + "." + "c" * 20
    assert "…[redacted]" in redact(long_jwt)


def test_turn_cap_applied() -> None:
    """Prompts are capped at TURN_CAP (2000) characters at scan time."""
    assert TURN_CAP == 2000
    # redact() preserves length (it only swaps secret substrings); the cap is
    # applied in _scan_session when building the record's turns list.
    long_prompt = "x" * 5000
    assert len(redact(long_prompt)) == 5000


# ---------------------------------------------------------------- scan filters


def _base_summary(tmp_path: Path, **overrides) -> dict:
    base = {
        "session_kind": "interactive",
        "info": {"cwd": _PROJ_CWD, "git_root_dir": str(tmp_path)},
        "updated_at": "2026-01-02T00:00:00+00:00",
    }
    base.update(overrides)
    return base


def test_scan_keeps_interactive_session(tmp_path: Path) -> None:
    """A normal interactive session with human turns is kept."""
    grok_home = _grok_home(tmp_path)
    summary = _base_summary(tmp_path, id="s1", head_branch="main")
    _write_session(grok_home, "user", "s1", summary, ["turn one two", "turn two three"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"))
    records = scan.records
    assert len(records) == 1
    assert records[0].id == "s1"
    assert records[0].human_turns == 2


def test_scan_drops_subagent_headless_by_default(tmp_path: Path) -> None:
    """subagent and headless sessions are dropped unless included."""
    grok_home = _grok_home(tmp_path)
    _write_session(grok_home, "user", "sub", _base_summary(tmp_path, id="sub", session_kind="subagent"), ["hi"])
    _write_session(grok_home, "user", "hl", _base_summary(tmp_path, id="hl", session_kind="headless"), ["hi"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"))
    assert [r.id for r in scan.records] == []
    # one subagent + one headless session, both dropped
    assert scan.sessions_seen == 2
    assert dict(scan.dropped).get("subagent") == 1
    assert dict(scan.dropped).get("headless") == 1


def test_scan_includes_headless_when_requested(tmp_path: Path) -> None:
    """--include-headless keeps headless sessions."""
    grok_home = _grok_home(tmp_path)
    _write_session(grok_home, "user", "hl", _base_summary(tmp_path, id="hl", session_kind="headless"), ["headless turn check"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"), include_headless=True)
    assert [r.id for r in scan.records] == ["hl"]


def test_scan_drops_temp_cwd_and_grok_e2e(tmp_path: Path) -> None:
    """temp cwd and grok-e2e cwd sessions are excluded."""
    grok_home = _grok_home(tmp_path)
    _write_session(grok_home, "user", "tmp", _base_summary(tmp_path, id="tmp", info={"cwd": "/tmp/fixture", "git_root_dir": ""}), ["x"])
    _write_session(
        grok_home,
        "user",
        "e2e",
        _base_summary(tmp_path, id="e2e", info={"cwd": "/tmp/grok-e2e-foo", "git_root_dir": ""}),
        ["y"],
    )
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"))
    assert [r.id for r in scan.records] == []


def test_scan_min_turns_filter(tmp_path: Path) -> None:
    """sessions below min_turns are dropped."""
    grok_home = _grok_home(tmp_path)
    _write_session(grok_home, "user", "a", _base_summary(tmp_path, id="a"), ["one alpha beta"])
    _write_session(grok_home, "user", "b", _base_summary(tmp_path, id="b"), ["one alpha beta", "two beta gamma", "three gamma delta"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"), min_turns=2)
    assert [r.id for r in scan.records] == ["b"]
    assert dict(scan.dropped).get("no_human_turns") == 1


def test_scan_days_window(tmp_path: Path) -> None:
    """--days keeps only recently-updated sessions."""
    import datetime as dt

    grok_home = _grok_home(tmp_path)
    now = dt.datetime.now(dt.UTC)
    _write_session(grok_home, "user", "new", _base_summary(tmp_path, id="new", updated_at=now.isoformat()), ["x alpha beta"])
    _write_session(grok_home, "user", "old", _base_summary(tmp_path, id="old", updated_at="2026-01-01T00:00:00+00:00"), ["y gamma delta"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"), days=1)
    assert [r.id for r in scan.records] == ["new"]


def test_scan_limit(tmp_path: Path) -> None:
    """--limit caps the kept count."""
    import datetime as dt

    grok_home = _grok_home(tmp_path)
    now = dt.datetime.now(dt.UTC)
    _write_session(grok_home, "user", "a", _base_summary(tmp_path, id="a", updated_at=now.isoformat()), ["a alpha beta"])
    _write_session(grok_home, "user", "b", _base_summary(tmp_path, id="b", updated_at="2026-01-02T00:00:00+00:00"), ["b beta gamma"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"), limit=1)
    assert [r.id for r in scan.records] == ["a"]
    assert dict(scan.dropped).get("beyond_limit") == 1


def test_scan_excludes_repeated_single_turn(tmp_path: Path) -> None:
    """a single identical prompt repeated 3+ times is treated as automation."""
    grok_home = _grok_home(tmp_path)
    for i in range(3):
        _write_session(grok_home, "user", f"s{i}", _base_summary(tmp_path, id=f"s{i}"), ["the same prompt"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"))
    assert [r.id for r in scan.records] == []
    assert scan.sessions_seen == 3


# ---------------------------------------------------------------- run-dir writing


def test_scan_writes_manifest_and_session_files(tmp_path: Path) -> None:
    """scan_sessions writes manifest.json and sessions/NNNN-<id>.json."""
    grok_home = _grok_home(tmp_path)
    run_dir = tmp_path / "run"
    summary = _base_summary(tmp_path, id="s1", head_branch="main")
    _write_session(grok_home, "user", "s1", summary, ["keep this turn"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(run_dir))
    assert len(scan.records) == 1
    assert scan.sessions_seen == 1
    assert scan.dropped == {}
    assert (run_dir / "manifest.json").is_file()
    session_files = list((run_dir / "sessions").iterdir())
    assert len(session_files) == 1
    assert session_files[0].name.startswith("0000-s1")
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sessions_kept"] == 1


def test_scan_returns_vos_not_raw_dicts(tmp_path: Path) -> None:
    """scan_sessions returns TraceSessionRecord VOs, not raw dicts."""
    grok_home = _grok_home(tmp_path)
    summary = _base_summary(tmp_path, id="s1")
    _write_session(grok_home, "user", "s1", summary, ["keep this turn"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"))
    assert isinstance(scan, ScanResult)
    assert all(isinstance(r, TraceSessionRecord) for r in scan.records)
    assert scan.records[0].turns == ("keep this turn",)


# ---------------------------------------------------------------- usage builder


def test_build_usage_hit_counts_and_sessions(tmp_path: Path) -> None:
    """skill hit counts, sessions, and last_used aggregate from records."""
    grok_home = _grok_home(tmp_path)
    run_dir = tmp_path / "run"
    (run_dir / "sessions").mkdir(parents=True)
    rec = {
        "id": "s1",
        "updated_at": "2026-01-02T00:00:00+00:00",
        "skills_loaded": {"lint": 2, "fmt": 1},
    }
    (run_dir / "sessions" / "0000-s1.json").write_text(json.dumps(rec), encoding="utf-8")

    (grok_home / "skills" / "cat" / "lint").mkdir(parents=True)
    (grok_home / "skills" / "cat" / "lint" / "SKILL.md").write_text("---\nname: lint\ndescription: lints\n---\n", encoding="utf-8")
    (grok_home / "skills" / "cat" / "fmt").mkdir(parents=True)
    (grok_home / "skills" / "cat" / "fmt" / "SKILL.md").write_text("---\nname: fmt\ndescription: fmt\n---\n", encoding="utf-8")
    (grok_home / "slash-mru.json").write_text(json.dumps({"by_command": {}}), encoding="utf-8")

    tracker = _make_tracker()
    report = tracker.build_usage(str(grok_home), str(run_dir))
    assert isinstance(report, UsageReport)
    by_name = {i.name: i for i in report.items}
    assert by_name["lint"].count == 2
    assert by_name["lint"].sessions == ("s1",)
    assert by_name["fmt"].count == 1


def test_unused_loaded_excludes_in_slash_mru(tmp_path: Path) -> None:
    """a loaded, zero-hit skill in slash-mru is NOT unused_loaded."""
    grok_home = _grok_home(tmp_path)
    run_dir = tmp_path / "run"
    (run_dir / "sessions").mkdir(parents=True)
    (grok_home / "skills" / "cat" / "used").mkdir(parents=True)
    (grok_home / "skills" / "cat" / "used" / "SKILL.md").write_text(
        "---\nname: used\ndescription: used skill\n---\n", encoding="utf-8"
    )
    (grok_home / "skills" / "cat" / "unused").mkdir(parents=True)
    (grok_home / "skills" / "cat" / "unused" / "SKILL.md").write_text(
        "---\nname: unused\ndescription: unused skill\n---\n", encoding="utf-8"
    )
    (grok_home / "slash-mru.json").write_text(
        json.dumps({"by_command": {"unused": {}}}), encoding="utf-8"
    )
    tracker = _make_tracker()
    report = tracker.build_usage(str(grok_home), str(run_dir))
    assert report.unused_loaded == ("used",)


def test_build_usage_returns_items_as_skill_usage_item_vos(tmp_path: Path) -> None:
    """build_usage returns SkillUsageItem VOs."""
    grok_home = _grok_home(tmp_path)
    run_dir = tmp_path / "run"
    (run_dir / "sessions").mkdir(parents=True)
    (grok_home / "skills" / "cat" / "lint").mkdir(parents=True)
    (grok_home / "skills" / "cat" / "lint" / "SKILL.md").write_text(
        "---\nname: lint\ndescription: lints\n---\n", encoding="utf-8"
    )
    (grok_home / "slash-mru.json").write_text(json.dumps({"by_command": {}}), encoding="utf-8")
    tracker = _make_tracker()
    report = tracker.build_usage(str(grok_home), str(run_dir))
    assert all(isinstance(i, SkillUsageItem) for i in report.items)
    assert report.kept_sessions == 0


def test_build_usage_kept_sessions_counts_records(tmp_path: Path) -> None:
    """kept_sessions is the number of kept session records, not distinct skills."""
    grok_home = _grok_home(tmp_path)
    run_dir = tmp_path / "run"
    (run_dir / "sessions").mkdir(parents=True)
    # two records, only one references a skill that is on disk
    for i, sid in enumerate(("s1", "s2")):
        rec = {
            "id": sid,
            "updated_at": "2026-01-02T00:00:00+00:00",
            "skills_loaded": {"lint": 1},
        }
        (run_dir / "sessions" / f"{i:04d}-{sid}.json").write_text(
            json.dumps(rec), encoding="utf-8"
        )
    (grok_home / "skills" / "cat" / "lint").mkdir(parents=True)
    (grok_home / "skills" / "cat" / "lint" / "SKILL.md").write_text(
        "---\nname: lint\ndescription: lints\n---\n", encoding="utf-8"
    )
    (grok_home / "slash-mru.json").write_text(json.dumps({"by_command": {}}), encoding="utf-8")
    tracker = _make_tracker()
    report = tracker.build_usage(str(grok_home), str(run_dir))
    assert report.kept_sessions == 2


def test_scan_drops_smoke_test_session(tmp_path: Path) -> None:
    """a smoke-test session (zero real tools, all turns < 3 words) is dropped."""
    grok_home = _grok_home(tmp_path)
    _write_session(grok_home, "user", "s1", _base_summary(tmp_path, id="s1"), ["hi", "ok"])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"))
    assert [r.id for r in scan.records] == []
    assert scan.sessions_seen == 1


def test_scan_caps_prompts_at_turn_cap(tmp_path: Path) -> None:
    """prompts longer than TURN_CAP are truncated at scan time."""
    grok_home = _grok_home(tmp_path)
    long_prompt = "aaa bbb " + "x" * 5000
    _write_session(grok_home, "user", "s1", _base_summary(tmp_path, id="s1"), [long_prompt])
    tracker = _make_tracker()
    scan = tracker.scan_sessions(str(grok_home), str(tmp_path / "run"))
    assert len(scan.records) == 1
    assert len(scan.records[0].turns[0]) <= TURN_CAP + len("…")



