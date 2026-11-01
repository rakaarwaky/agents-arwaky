"""Unit tests for ``capabilities_skills_state.SkillsTraceState``.

Status transitions, trash path-shape guard (valid + refused shapes), decide
log shape, wait exit-code semantics (0 ready / 3 report-stall / 4 phase-stall /
2 deadline), and restrict. All under ``tmp_path`` — no real GROK_HOME.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import pytest

from modules.shared.src.skills.taxonomy_skills_vo import (
    TraceDecision,
    TraceStateStatus,
)
from modules.skills.src.capabilities_skills_state import (
    STATUSES,
    SkillsTraceState,
    decisions_path,
    files_ready,
    latest_synthesis,
    load_state,
    mark,
    newest_mtime,
    save_state,
    state_path,
)


def _grok_home(tmp_path: Path) -> Path:
    return tmp_path / "grok"


def _state(tmp_path: Path) -> SkillsTraceState:
    return SkillsTraceState()


# ---------------------------------------------------------------- protocol / helpers


def test_state_implements_protocol() -> None:
    """SkillsTraceState satisfies the IStateProtocol contract."""
    from modules.shared.src.skills.contract_skills_protocol import IStateProtocol

    assert isinstance(SkillsTraceState(), IStateProtocol)


def test_status_machine_values() -> None:
    """STATUSES matches the collected → running → report_ready → curating → done flow."""
    assert [s.value for s in STATUSES] == [
        "collected",
        "running",
        "report_ready",
        "curating",
        "done",
    ]


def test_state_path_and_atomic_save(tmp_path: Path) -> None:
    """state_path + save_state write atomically via tmp + os.replace."""
    grok_home = _grok_home(tmp_path)
    path = state_path(str(grok_home))
    save_state(path, {"pending": {"status": "collected"}})
    assert Path(path).is_file()
    assert not Path(path + ".tmp").is_file()
    assert load_state(path)["pending"]["status"] == "collected"


# ---------------------------------------------------------------- set_status / get_status


def test_set_status_collected_then_done_stamps_last_completed(tmp_path: Path) -> None:
    """set_status moves through the machine; done stamps last_completed_*."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    run_dir = str(tmp_path / "run")
    got = state.set_status(str(grok_home), run_dir, TraceStateStatus.COLLECTED)
    assert got == TraceStateStatus.COLLECTED

    got = state.set_status(str(grok_home), run_dir, TraceStateStatus.DONE)
    assert got == TraceStateStatus.DONE
    st = load_state(state_path(str(grok_home)))
    assert st["last_completed_at"]
    assert st["last_completed_dir"] == run_dir


def test_get_status_pending_returns_status(tmp_path: Path) -> None:
    """get_status returns the pending status."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    run_dir = str(tmp_path / "run")
    state.set_status(str(grok_home), run_dir, TraceStateStatus.RUNNING)
    status, _view = state.get_status(str(grok_home))
    assert status == TraceStateStatus.RUNNING


# ---------------------------------------------------------------- mark / files_ready


def test_mark_done_stamps_last_completed(tmp_path: Path) -> None:
    """mark with done stamps last_completed_at / last_completed_dir."""
    grok_home = _grok_home(tmp_path)
    path = state_path(str(grok_home))
    run_dir = str(tmp_path / "run")
    mark(path, run_dir, TraceStateStatus.DONE)
    st = load_state(path)
    assert st["last_completed_dir"] == run_dir


def test_files_ready_true_false() -> None:
    """files_ready requires both report.md and actions.json."""

    with tempfile.TemporaryDirectory() as d:
        assert not files_ready(d)
        Path(d, "report.md").write_text("x")
        assert not files_ready(d)
        Path(d, "actions.json").write_text("{}")
        assert files_ready(d)


# ---------------------------------------------------------------- trash path-shape guard


def _make_trash_shape(grok_home: Path, kind: str, name: str) -> Path:
    if kind == "skill":
        p = grok_home / "skills" / name
        p.mkdir(parents=True)
        (p / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
        return p
    if kind == "workflow":
        w = grok_home / "workflows"
        w.mkdir(parents=True)
        p = w / f"{name}.rhai"
        p.write_text("name: x\n", encoding="utf-8")
        return p
    if kind == "hook":
        h = grok_home / "hooks"
        h.mkdir(parents=True)
        p = h / f"{name}.py"
        p.write_text("print(1)\n", encoding="utf-8")
        return p
    raise ValueError(kind)


def test_trash_accepts_skill_directory(tmp_path: Path) -> None:
    """a skills/<name> directory under GROK_HOME is moved to learn/trash/<run>."""
    grok_home = _grok_home(tmp_path)
    skill = _make_trash_shape(grok_home, "skill", "obsolete-skill")
    state = _state(tmp_path)
    moved = state.trash(str(grok_home), "run-001", [str(skill)])
    assert not skill.exists()
    assert moved == (str(grok_home / "learn" / "trash" / "run-001" / "obsolete-skill"),)
    assert (grok_home / "learn" / "trash" / "run-001" / "obsolete-skill").is_dir()


def test_trash_accepts_workflow_file(tmp_path: Path) -> None:
    """a workflows/*.rhai file under GROK_HOME is moved."""
    grok_home = _grok_home(tmp_path)
    wf = _make_trash_shape(grok_home, "workflow", "learn-traces")
    state = _state(tmp_path)
    state.trash(str(grok_home), "run-001", [str(wf)])
    assert not wf.exists()
    assert (grok_home / "learn" / "trash" / "run-001" / "learn-traces.rhai").is_file()


def test_trash_accepts_hook_file(tmp_path: Path) -> None:
    """a hooks/* file under GROK_HOME is moved."""
    grok_home = _grok_home(tmp_path)
    hook = _make_trash_shape(grok_home, "hook", "pre-commit")
    state = _state(tmp_path)
    state.trash(str(grok_home), "run-001", [str(hook)])
    assert not hook.exists()
    assert (grok_home / "learn" / "trash" / "run-001" / "pre-commit.py").is_file()


def test_trash_refuses_multi_component_run_name(tmp_path: Path) -> None:
    """trash refuses a run_name containing a path separator."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    with pytest.raises(ValueError, match="single path component"):
        state.trash(str(grok_home), "a/b", [str(tmp_path / "x")])


def test_trash_refuses_arbitrary_path(tmp_path: Path) -> None:
    """trash refuses paths that are not skills/workflows/hooks shapes."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    weird = tmp_path / "sessions" / "user" / "sess-001"
    weird.mkdir(parents=True)
    with pytest.raises(ValueError, match="refusing"):
        state.trash(str(grok_home), "run-001", [str(weird)])


def test_trash_refuses_missing_path(tmp_path: Path) -> None:
    """trash refuses a path that does not exist."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    with pytest.raises(FileNotFoundError, match="missing"):
        state.trash(str(grok_home), "run-001", [str(tmp_path / "nope")])


def test_trash_under_project_grok_and_agents(tmp_path: Path) -> None:
    """a skills dir under a project .grok (or ~/.agents) is accepted."""
    grok_home = _grok_home(tmp_path)
    project_grok = tmp_path / "proj" / ".grok"
    skill = project_grok / "skills" / "proj-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: proj-skill\n---\n", encoding="utf-8")
    state = _state(tmp_path)
    moved = state.trash(str(grok_home), "run-001", [str(skill)])
    assert not skill.exists()
    assert moved[0].endswith(os.path.join("learn", "trash", "run-001", "proj-skill"))


# ---------------------------------------------------------------- decide


def test_decide_appends_jsonl_in_legacy_key_order(tmp_path: Path) -> None:
    """decide appends one line to learn/decisions.jsonl with legacy key order."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    run_dir = str(tmp_path / "run")
    decision = TraceDecision(
        date="2026-11-01",
        run_dir=run_dir,
        decision_id="A3",
        kind="skill",
        action="delete",
        target="old-skill",
        target_path=str(tmp_path / "old-skill"),
        decision="applied",
        undo=None,
    )
    got = state.decide(str(grok_home), run_dir, decision)
    assert got == decision

    dec_path = Path(decisions_path(str(grok_home)))
    assert dec_path.is_file()
    line = json.loads(dec_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    # legacy key order: date, run_dir, id, kind, action, target, path, decision, undo
    assert list(line.keys()) == [
        "date",
        "run_dir",
        "id",
        "kind",
        "action",
        "target",
        "path",
        "decision",
        "undo",
    ]
    assert line["id"] == "A3"
    assert line["decision"] == "applied"


def test_decide_undo_preserved(tmp_path: Path) -> None:
    """the undo field is written when present."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    run_dir = str(tmp_path / "run")
    decision = TraceDecision(
        date="2026-11-01",
        run_dir=run_dir,
        decision_id="A4",
        kind="skill",
        action="create",
        target="new-skill",
        target_path=str(tmp_path / "new-skill"),
        decision="rejected",
        undo="/prev",
    )
    state.decide(str(grok_home), run_dir, decision)
    line = json.loads(Path(decisions_path(str(grok_home))).read_text(encoding="utf-8").strip().splitlines()[-1])
    assert line["undo"] == "/prev"


# ---------------------------------------------------------------- wait


def test_wait_returns_report_ready_when_files_exist(tmp_path: Path) -> None:
    """report.md + actions.json present → report_ready (exit 0)."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    run_dir = str(tmp_path / "run")
    Path(run_dir).mkdir(parents=True)
    Path(run_dir, "report.md").write_text("report")
    Path(run_dir, "actions.json").write_text("{}")
    status = state.wait(str(grok_home), run_dir, timeout_min=1)
    assert status == TraceStateStatus.REPORT_READY


def test_wait_deadline_maps_to_exit_2(tmp_path: Path, monkeypatch) -> None:
    """deadline exceeded → DEADLINE (surface maps to exit 2)."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    run_dir = str(tmp_path / "run")
    Path(run_dir).mkdir(parents=True)
    # noop sleep so the loop spins without real waiting; timeout_min=0 hits deadline immediately
    monkeypatch.setattr(time, "sleep", lambda *a: None)
    status = state.wait(str(grok_home), run_dir, timeout_min=0)
    assert status == TraceStateStatus.DEADLINE


def test_wait_sets_report_ready_mark(tmp_path: Path) -> None:
    """on success the pending run is marked report_ready in state.json."""
    grok_home = _grok_home(tmp_path)
    state = _state(tmp_path)
    run_dir = str(tmp_path / "run")
    Path(run_dir).mkdir(parents=True)
    Path(run_dir, "report.md").write_text("report")
    Path(run_dir, "actions.json").write_text("{}")
    state.wait(str(grok_home), run_dir, timeout_min=1)
    st = load_state(state_path(str(grok_home)))
    assert st["pending"]["status"] == TraceStateStatus.REPORT_READY.value


# ---------------------------------------------------------------- restrict


def test_restrict_chmod_0600(tmp_path: Path) -> None:
    """restrict sets owner-only permissions where the OS supports it."""
    p = tmp_path / "secret.json"
    p.write_text("{}")
    state = _state(tmp_path)
    restricted = state.restrict([str(p)])
    assert restricted == (str(p),)
    mode = p.stat().st_mode & 0o777
    assert mode == 0o600


# ---------------------------------------------------------------- module helpers


def test_newest_mtime_and_latest_synthesis(tmp_path: Path) -> None:
    """newest_mtime / latest_synthesis over a run dir."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "a.md").write_text("a")
    (run_dir / "reduce").mkdir()
    (run_dir / "reduce" / "r1.md").write_text("r1")
    (run_dir / "reduce" / "r2.md").write_text("r2")
    assert newest_mtime(str(run_dir)) >= 0
    assert latest_synthesis(str(run_dir)).endswith("reduce/r2.md")
    assert latest_synthesis(str(tmp_path / "none")) is None


def test_status_enum_is_str_enum() -> None:
    """TraceStateStatus is a StrEnum (comparable to str)."""
    assert TraceStateStatus.DONE == "done"
    assert TraceStateStatus("running") == TraceStateStatus.RUNNING


def test_trace_decision_is_frozen() -> None:
    """TraceDecision is immutable."""
    d = TraceDecision(
        date="2026-11-01",
        run_dir="/run",
        decision_id="A1",
        kind="skill",
        action="create",
        target="x",
        target_path="/x",
        decision="applied",
    )
    with pytest.raises(AttributeError):
        d.decision = "rejected"  # type: ignore[misc]
