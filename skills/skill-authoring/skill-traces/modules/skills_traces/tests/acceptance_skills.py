"""Acceptance tests — map 1:1 to business requirements (FRD/PRD IDs)."""
from __future__ import annotations

from pathlib import Path


def _make_agent() -> object:
    from skills_traces.src.agent_skills_orchestrator import SkillsAgent
    from skills_traces.src.capabilities_skills_scan import SkillsTracesScan
    from skills_traces.src.capabilities_skills_state import SkillsTracesState

    return SkillsAgent(scan=SkillsTracesScan(), state=SkillsTracesState())


def _grok_home(tmp_path: Path) -> Path:
    grok_home = tmp_path / "grok"
    (grok_home / "learn").mkdir(parents=True)
    return grok_home


def test_acceptance_fr_trace_collect(tmp_path: Path):
    """AC-TRACE-001: collect scans sessions and builds usage report."""
    from shared.src.skills_traces.taxonomy_skills_request import (
        SkillsOp,
        SkillsRequest,
    )

    agent = _make_agent()
    grok_home = _grok_home(tmp_path)
    sessions = grok_home / "sessions" / "user" / "sess-001"
    sessions.mkdir(parents=True)
    (sessions / "summary.json").write_text(
        '{"id":"sess-001","session_kind":"interactive",'
        '"info":{"cwd":"/home/raka/proj","git_root_dir":"/home/raka/proj"},'
        '"updated_at":"2026-01-02T00:00:00+00:00"}',
        encoding="utf-8",
    )
    (sessions / "chat_history.jsonl").write_text(
        '{"type":"user","content":"<user_query>turn one two three</user_query>",'
        '"synthetic_reason":null}\n',
        encoding="utf-8",
    )

    run_dir = tmp_path / "run"
    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "collect",
                "grok_home": str(grok_home),
                "run_dir": str(run_dir),
                "days": "0",
                "since_last": "0",
                "min_turns": "1",
                "limit": "0",
            },
        )
    )
    assert result.ok
    assert result.usage is not None
    assert result.collect_summary is not None
    assert result.collect_summary.sessions_seen == 1


def test_acceptance_fr_trace_usage(tmp_path: Path):
    """AC-TRACE-002: usage reads the last run's skills-only usage report."""
    from shared.src.skills_traces.taxonomy_skills_request import (
        SkillsOp,
        SkillsRequest,
    )

    agent = _make_agent()
    grok_home = _grok_home(tmp_path)
    run_dir = tmp_path / "run"
    (run_dir / "sessions").mkdir(parents=True)
    (run_dir / "sessions" / "0000-s1.json").write_text(
        '{"id":"s1","updated_at":"2026-01-02T00:00:00+00:00",'
        '"skills_loaded":{"lint":2}}',
        encoding="utf-8",
    )
    (grok_home / "skills" / "cat" / "lint").mkdir(parents=True)
    (grok_home / "skills" / "cat" / "lint" / "SKILL.md").write_text(
        "---\nname: lint\ndescription: lints\n---\n", encoding="utf-8"
    )
    (grok_home / "slash-mru.json").write_text('{"by_command":{}}', encoding="utf-8")

    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={"traces_action": "usage", "grok_home": str(grok_home), "run_dir": str(run_dir)},
        )
    )
    assert result.ok
    assert result.usage is not None
    assert result.usage.kept_sessions == 1
    assert {i.name for i in result.usage.items} == {"lint"}


def test_acceptance_fr_trace_phrases(tmp_path: Path):
    """AC-TRACE-003: phrases mines repeated exact prompts across sessions."""
    from shared.src.skills_traces.taxonomy_skills_request import (
        SkillsOp,
        SkillsRequest,
    )

    agent = _make_agent()
    grok_home = _grok_home(tmp_path)
    run_dir = tmp_path / "run"
    (run_dir / "sessions").mkdir(parents=True)
    for i in range(2):
        (run_dir / "sessions" / f"{i}.json").write_text(
            f'{{"id":"s{i}","turns":["please refactor the login handler"],'
            '"repeated_single_turn":false}',
            encoding="utf-8",
        )

    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={"traces_action": "phrases", "grok_home": str(grok_home), "run_dir": str(run_dir)},
        )
    )
    assert result.ok
    assert result.phrases is not None
    assert len(result.phrases.exact_prompts) == 1
    assert result.phrases.exact_prompts[0].phrase == "please refactor the login handler"


def test_acceptance_fr_trace_state_wait_ready(tmp_path: Path):
    """AC-TRACE-004: state wait returns report_ready (exit 0) when files exist."""
    from shared.src.skills_traces.taxonomy_skills_request import (
        SkillsOp,
        SkillsRequest,
    )

    agent = _make_agent()
    grok_home = _grok_home(tmp_path)
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "report.md").write_text("report")
    (run_dir / "actions.json").write_text("{}")

    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "state",
                "grok_home": str(grok_home),
                "run_dir": str(run_dir),
                "state_action": "wait",
                "timeout_min": "1",
            },
        )
    )
    assert result.ok
    assert result.state_status.value == "report_ready"
