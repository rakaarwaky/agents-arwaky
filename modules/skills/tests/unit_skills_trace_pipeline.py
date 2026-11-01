"""Unit tests for the shared trace-learning pipeline scripts.

Follows the existing conventions in ``modules/skills/tests``:
``tmp_path`` builds a fake ``GROK_HOME``, and the scripts are invoked
through ``subprocess`` so their real CLI surface (argparse, exit codes)
is exercised end-to-end.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PIPELINE = REPO_ROOT / "skills" / "skill-authoring" / "_trace-pipeline"
# pr-5 moved the canonical workflow out of _trace-pipeline to the repo-top-level workflows dir
CANONICAL_WORKFLOW = REPO_ROOT / "workflows" / "learn-traces.rhai"
COLLECT = PIPELINE / "scripts" / "collect_sessions.py"
STATE = PIPELINE / "scripts" / "state.py"
PYTHON = sys.executable


def fake_grok_home(tmp_path: Path) -> Path:
    """Build a minimal GROK_HOME with a sessions/ tree and a state.json."""
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
                "info": {"cwd": str(tmp_path), "git_root_dir": str(tmp_path)},
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
    (grok_home / "workflows").mkdir(parents=True)
    return grok_home


def run_collect(grok_home: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(COLLECT), "--grok-home", str(grok_home), *flags],
        capture_output=True,
        text=True,
    )


def run_state(grok_home: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(STATE), "--grok-home", str(grok_home), *flags],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------- (a) argument parsing


def test_collect_accepts_every_real_flag(tmp_path: Path) -> None:
    """Each real flag of ``collect_sessions.py`` is accepted (no argparse error)."""
    grok_home = fake_grok_home(tmp_path)
    real_flags = [
        "--days", "1",
        "--since-last",
        "--include-headless",
        "--include-subagents",
        "--cwd", str(tmp_path),
        "--exclude-cwd", str(tmp_path / "exclude"),
        "--drop-pattern", r"^/feedback",
        "--min-turns", "1",
        "--session-id", "sess-001",
        "--limit", "5",
        "--estimate",
        "--batch", "10",
    ]
    proc = run_collect(grok_home, *real_flags)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert "windows" in payload


def test_collect_rejects_unknown_flag(tmp_path: Path) -> None:
    """A fake unknown flag is rejected by argparse (exit 2)."""
    grok_home = fake_grok_home(tmp_path)
    proc = run_collect(grok_home, "--mode", "step")
    assert proc.returncode == 2
    assert "unrecognized arguments" in proc.stderr

    proc = run_collect(grok_home, "--focus", "text")
    assert proc.returncode == 2

    proc = run_collect(grok_home, "--resume")
    assert proc.returncode == 2

    proc = run_collect(grok_home, "--per-trace")
    assert proc.returncode == 2


def test_collect_estimate_writes_estimate_json(tmp_path: Path) -> None:
    """``--estimate`` scans everything and writes only estimate.json."""
    grok_home = fake_grok_home(tmp_path)
    out = grok_home / "learn" / "runs" / "estimate"
    proc = run_collect(grok_home, "--out", str(out), "--estimate")
    assert proc.returncode == 0, proc.stderr
    assert (out / "estimate.json").is_file()
    assert not (out / "sessions").exists()


# ---------------------------------------------------------------- (b) retire_stale_workflow_copy


def test_retire_stale_workflow_copy_identical_returns_none(tmp_path: Path) -> None:
    """User copy identical to skill copy -> None, nothing moved."""
    grok_home = fake_grok_home(tmp_path)
    skill_copy = CANONICAL_WORKFLOW
    user_copy = grok_home / "workflows" / "learn-traces.rhai"
    shutil.copyfile(skill_copy, user_copy)

    proc = run_collect(grok_home, "--estimate")
    assert proc.returncode == 0, proc.stderr
    assert user_copy.is_file()


def test_retire_stale_workflow_copy_different_moves_to_trash(tmp_path: Path) -> None:
    """User copy present and different -> moved to trash; absent -> None."""
    grok_home = fake_grok_home(tmp_path)
    user_copy = grok_home / "workflows" / "learn-traces.rhai"
    user_copy.write_text('name: "learn-traces"\n// stale copy\n', encoding="utf-8")

    proc = run_collect(grok_home, "--estimate")
    assert proc.returncode == 0, proc.stderr
    assert not user_copy.is_file()
    trash_dirs = list((grok_home / "learn" / "trash").iterdir())
    assert any(p.name.endswith("-stale-workflow") for p in trash_dirs)


def test_retire_stale_workflow_copy_absent_returns_none(tmp_path: Path) -> None:
    """No user copy -> None, no error."""
    grok_home = fake_grok_home(tmp_path)
    proc = run_collect(grok_home, "--estimate")
    assert proc.returncode == 0, proc.stderr


# ---------------------------------------------------------------- (c) state.py get exit codes


def test_state_get_exit_3_when_run_pending(tmp_path: Path) -> None:
    """``state.py get`` exits 3 when a run is pending (status != done)."""
    grok_home = fake_grok_home(tmp_path)
    proc = run_state(grok_home, "set", "--run-dir", str(tmp_path / "run"), "--status", "collected")
    assert proc.returncode == 0, proc.stderr

    proc = run_state(grok_home, "get")
    assert proc.returncode == 3


def test_state_get_exit_0_when_not_pending(tmp_path: Path) -> None:
    """``state.py get`` exits 0 when nothing is pending."""
    grok_home = fake_grok_home(tmp_path)
    proc = run_state(grok_home, "get")
    assert proc.returncode == 0


# ---------------------------------------------------------------- (d) state.py decide


def test_state_decide_appends_well_formed_jsonl(tmp_path: Path) -> None:
    """``state.py decide`` appends one JSON line to learn/decisions.jsonl."""
    grok_home = fake_grok_home(tmp_path)
    run_dir = grok_home / "learn" / "runs" / "run-001"
    run_dir.mkdir(parents=True)

    proc = run_state(
        grok_home,
        "decide",
        "--run-dir",
        str(run_dir),
        "--id",
        "A1",
        "--kind",
        "skill",
        "--action",
        "create",
        "--target",
        "new-skill",
        "--path",
        str(run_dir / "new-skill"),
        "--decision",
        "applied",
    )
    assert proc.returncode == 0, proc.stderr

    decisions = grok_home / "learn" / "decisions.jsonl"
    assert decisions.is_file()
    line = json.loads(decisions.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert line["id"] == "A1"
    assert line["kind"] == "skill"
    assert line["action"] == "create"
    assert line["target"] == "new-skill"
    assert line["decision"] == "applied"
    assert line["run_dir"] == str(run_dir)


# ---------------------------------------------------------------- (e) state.py trash


def test_state_trash_refuses_path_separator(tmp_path: Path) -> None:
    """``trash`` refuses a --run-name containing a path separator."""
    grok_home = fake_grok_home(tmp_path)
    proc = run_state(grok_home, "trash", "--run-name", "a/b", str(tmp_path / "x"))
    assert proc.returncode == 2
    assert "run-name must be a single path component" in proc.stdout


def test_state_trash_accepts_skills_name_directory(tmp_path: Path) -> None:
    """``trash`` accepts a ``skills/<name>`` directory under GROK_HOME."""
    grok_home = fake_grok_home(tmp_path)
    skills_dir = grok_home / "skills" / "obsolete-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("---\nname: obsolete-skill\n---\n", encoding="utf-8")

    proc = run_state(grok_home, "trash", "--run-name", "run-001", str(skills_dir))
    assert proc.returncode == 0, proc.stderr
    assert not skills_dir.exists()
    trash_file = grok_home / "learn" / "trash" / "run-001" / "obsolete-skill"
    assert trash_file.is_dir()
