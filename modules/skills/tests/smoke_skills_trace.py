"""Smoke tests for the trace verbs — exit 0 on a minimal fixture."""

from __future__ import annotations

import json
from pathlib import Path

from modules.cli.src.surface_skills_command import cmd_skills
from modules.skills.src.root_skills_container import default_aggregate
from modules.skills.tests.fixture_skills import run_surface


def _make_grok_home(tmp_path: Path) -> Path:
    grok_home = tmp_path / "grok"
    sessions = grok_home / "sessions" / "user" / "sess-001"
    sessions.mkdir(parents=True)
    (sessions / "summary.json").write_text(
        json.dumps(
            {
                "id": "sess-001",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-02T00:00:00+00:00",
                "session_kind": "interactive",
                "info": {
                    "cwd": str(tmp_path / "proj"),
                    "git_root_dir": str(tmp_path / "proj"),
                },
                "head_branch": "main",
                "generated_title": "test session",
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    (sessions / "chat_history.jsonl").write_text(
        json.dumps(
            {
                "type": "user",
                "content": '<user_query>turn one</user_query>',
                "synthetic_reason": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (grok_home / "learn").mkdir(parents=True)
    return grok_home


def test_smoke_trace_collect_exits_0(tmp_path: Path) -> None:
    """SM-TRACE-001: trace-collect exits 0 on a minimal fixture."""
    grok_home = _make_grok_home(tmp_path)
    run_dir = tmp_path / "run"
    code, _out, _err = run_surface(
        grok_home,
        "trace-collect",
        "--grok-home",
        str(grok_home),
        "--out",
        str(run_dir),
    )
    assert code == 0


def test_smoke_trace_usage_exits_0(tmp_path: Path) -> None:
    """SM-TRACE-002: trace-usage exits 0 on a minimal fixture."""
    grok_home = _make_grok_home(tmp_path)
    run_dir = tmp_path / "run"
    run_surface(
        grok_home,
        "trace-collect",
        "--grok-home",
        str(grok_home),
        "--out",
        str(run_dir),
    )
    code, _out, _err = run_surface(
        grok_home,
        "trace-usage",
        "--grok-home",
        str(grok_home),
        "--run-dir",
        str(run_dir),
    )
    assert code == 0


def test_smoke_trace_phrases_exits_0(tmp_path: Path) -> None:
    """SM-TRACE-003: trace-phrases exits 0 on a minimal fixture."""
    grok_home = _make_grok_home(tmp_path)
    run_dir = tmp_path / "run"
    run_surface(
        grok_home,
        "trace-collect",
        "--grok-home",
        str(grok_home),
        "--out",
        str(run_dir),
    )
    code, _out, _err = run_surface(
        grok_home,
        "trace-phrases",
        "--run-dir",
        str(run_dir),
    )
    assert code == 0


def test_smoke_trace_state_get_exits_3_when_pending(tmp_path: Path) -> None:
    """SM-TRACE-004: trace-state get exits 3 while a run is pending."""
    grok_home = _make_grok_home(tmp_path)
    run_dir = tmp_path / "run"
    run_surface(
        grok_home,
        "trace-state",
        "set",
        "--grok-home",
        str(grok_home),
        "--run-dir",
        str(run_dir),
        "--status",
        "collected",
    )
    code = run_surface(
        grok_home,
        "trace-state",
        "get",
        "--grok-home",
        str(grok_home),
    )
    assert code[0] == 3


def test_smoke_trace_state_wait_ready_exits_0(tmp_path: Path) -> None:
    """SM-TRACE-005: trace-state wait exits 0 when report.md + actions.json exist."""
    grok_home = _make_grok_home(tmp_path)
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "report.md").write_text("report")
    (run_dir / "actions.json").write_text("{}")
    code = run_surface(
        grok_home,
        "trace-state",
        "wait",
        "--grok-home",
        str(grok_home),
        "--run-dir",
        str(run_dir),
        "--timeout-min",
        "1",
    )
    assert code[0] == 0


def test_smoke_trace_verbs_parse_flags(tmp_path: Path) -> None:
    """SM-TRACE-006: all four trace verbs parse their flags (--help)."""

    for verb in ("trace-collect", "trace-usage", "trace-phrases"):
        assert cmd_skills([verb, "--help"], default_aggregate()) == 0
    assert cmd_skills(["trace-state", "wait", "--help"], default_aggregate()) == 0
