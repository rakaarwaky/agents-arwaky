"""E2E tests for the trace CLI verbs — drive cmd_skills directly over fixture trees.

Asserts exit codes + JSON shape for all four verbs without a real $GROK_HOME.
"""

from __future__ import annotations

import json
from pathlib import Path

from modules.cli.src.surface_skills_command import cmd_skills
from modules.skills.src.root_skills_container import default_aggregate
from modules.skills.tests.fixture_skills import make_grok_home, run_trace_surface


def test_e2e_trace_collect_exits_0_and_prints_run_dir(tmp_path: Path) -> None:
    """E2E-TRACE-001: trace-collect exits 0 and prints the run dir."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    code, out, _err = run_trace_surface(
        grok_home,
        "trace-collect",
        "--grok-home",
        str(grok_home),
        "--out",
        str(run_dir),
    )
    assert code == 0
    assert str(run_dir) in out
    assert (run_dir / "manifest.json").is_file()


def test_e2e_trace_collect_json_shape(tmp_path: Path) -> None:
    """E2E-TRACE-002: trace-collect --json emits {run_dir, kept, seen, dropped}."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    code, out, _err = run_trace_surface(
        grok_home,
        "trace-collect",
        "--grok-home",
        str(grok_home),
        "--out",
        str(run_dir),
        "--json",
    )
    assert code == 0
    payload = json.loads(out)
    assert list(payload) == ["run_dir", "kept", "seen", "dropped"]
    assert payload["run_dir"] == str(run_dir)
    # real scan counters, not constants: one session seen, one kept
    assert payload["seen"] == 1
    assert payload["kept"] == 1
    assert payload["dropped"] == {}


def test_e2e_trace_usage_exits_0(tmp_path: Path) -> None:
    """E2E-TRACE-003: trace-usage exits 0 after a collect."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    run_trace_surface(
        grok_home,
        "trace-collect",
        "--grok-home",
        str(grok_home),
        "--out",
        str(run_dir),
    )
    code, out, _err = run_trace_surface(
        grok_home,
        "trace-usage",
        "--grok-home",
        str(grok_home),
        "--run-dir",
        str(run_dir),
    )
    assert code == 0
    assert "Kept sessions:" in out


def test_e2e_trace_usage_json_shape(tmp_path: Path) -> None:
    """E2E-TRACE-004: trace-usage --json emits {kept_sessions, items, unused_loaded}."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    run_trace_surface(
        grok_home,
        "trace-collect",
        "--grok-home",
        str(grok_home),
        "--out",
        str(run_dir),
    )
    code, out, _err = run_trace_surface(
        grok_home,
        "trace-usage",
        "--grok-home",
        str(grok_home),
        "--run-dir",
        str(run_dir),
        "--json",
    )
    assert code == 0
    payload = json.loads(out)
    assert list(payload) == ["kept_sessions", "items", "unused_loaded"]


def test_e2e_trace_phrases_exits_0(tmp_path: Path) -> None:
    """E2E-TRACE-005: trace-phrases exits 0 over a fixture run dir."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    run_trace_surface(
        grok_home,
        "trace-collect",
        "--grok-home",
        str(grok_home),
        "--out",
        str(run_dir),
    )
    code, _out, _err = run_trace_surface(
        grok_home,
        "trace-phrases",
        "--run-dir",
        str(run_dir),
    )
    assert code == 0


def test_e2e_trace_phrases_json_shape(tmp_path: Path) -> None:
    """E2E-TRACE-006: trace-phrases --json emits the three phrase arrays."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    run_trace_surface(
        grok_home,
        "trace-collect",
        "--grok-home",
        str(grok_home),
        "--out",
        str(run_dir),
    )
    code, out, _err = run_trace_surface(
        grok_home,
        "trace-phrases",
        "--run-dir",
        str(run_dir),
        "--json",
    )
    assert code == 0
    payload = json.loads(out)
    assert list(payload) == ["exact_prompts", "stems", "repeated_instruction_lines"]


def test_e2e_trace_state_get_pending_exits_3(tmp_path: Path) -> None:
    """E2E-TRACE-007: trace-state get exits 3 while a run is pending."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    # set status to collected (pending)
    code = run_trace_surface(
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
    assert code[0] == 0

    # get while pending → exit 3
    code = run_trace_surface(
        grok_home,
        "trace-state",
        "get",
        "--grok-home",
        str(grok_home),
    )
    assert code[0] == 3


def test_e2e_trace_state_set_done_exits_0(tmp_path: Path) -> None:
    """E2E-TRACE-008: trace-state set exits 0."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    code = run_trace_surface(
        grok_home,
        "trace-state",
        "set",
        "--grok-home",
        str(grok_home),
        "--run-dir",
        str(run_dir),
        "--status",
        "done",
    )
    assert code[0] == 0


def test_e2e_trace_state_wait_report_ready_exits_0(tmp_path: Path) -> None:
    """E2E-TRACE-009: trace-state wait with report.md + actions.json → exit 0."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "report.md").write_text("report")
    (run_dir / "actions.json").write_text("{}")
    code = run_trace_surface(
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


def test_e2e_trace_state_wait_deadline_exits_2(tmp_path: Path, monkeypatch) -> None:
    """E2E-TRACE-010: trace-state wait deadline → exit 2."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    # noop sleep so the loop spins without real waiting; timeout_min=0 hits deadline immediately
    import time

    monkeypatch.setattr(time, "sleep", lambda *a: None)
    code = run_trace_surface(
        grok_home,
        "trace-state",
        "wait",
        "--grok-home",
        str(grok_home),
        "--run-dir",
        str(run_dir),
        "--timeout-min",
        "0",
    )
    assert code[0] == 2


def test_e2e_trace_verbs_registered_in_help(tmp_path: Path) -> None:
    """E2E-TRACE-011: all four trace verbs appear in the skills help."""

    import io
    from contextlib import redirect_stdout

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = cmd_skills([], default_aggregate())
    assert code == 0
    out = stdout.getvalue()
    for verb in ("trace-collect", "trace-usage", "trace-phrases", "trace-state"):
        assert verb in out


def test_e2e_trace_state_restrict_sets_mode_0600(tmp_path: Path) -> None:
    """E2E-TRACE-012: trace-state restrict chmods the target file to 0600."""
    import stat as stat_mod

    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj", with_skills=True)
    target = grok_home / "secret.txt"
    target.write_text("restricted", encoding="utf-8")
    target.chmod(0o644)  # start with a permissive mode

    code, out, _err = run_trace_surface(
        grok_home,
        "trace-state",
        "restrict",
        str(target),
    )
    assert code == 0
    assert str(target) in out
    assert stat_mod.S_IMODE(target.stat().st_mode) == 0o600
