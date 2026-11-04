"""Integration test: tracker + phrases + state wired through the agent.

A collect → phrases → state-set cycle over a fixture session tree (tmp_path,
NOT the real $GROK_HOME). Exercises the agent sequencing the traces
capability (which owns both the scan/usage/phrases half and the
state-lifecycle half) with the root wiring it.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.skills_traces.contract_skills_protocol import ISkillsTraceScanProtocol
from shared.src.skills_traces.taxonomy_skills_authoring_vo import (
    PhrasesReport,
    UsageReport,
)
from shared.src.skills_traces.taxonomy_skills_vo import (
    ScanResult,
    SkillsOp,
    SkillsRequest,
    TraceStateStatus,
)

from skills_traces.src.agent_skills_orchestrator import SkillsAgent
from skills_traces.src.capabilities_skills_traces import SkillsTraces
from skills_traces.tests.fixture_skills import make_grok_home


def _make_agent(root: Path) -> SkillsAgent:
    """Agent wired with the traces capability over a fixture root."""
    traces = SkillsTraces()
    return SkillsAgent(
        scan=traces,
        state=traces,
        default_root=root,
    )


def test_integration_trace_collect_then_phrases_then_state(tmp_path: Path) -> None:
    """INT-TRACE-001: collect → phrases → state-set cycle over a fixture tree."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj")
    run_dir = tmp_path / "run"
    agent = _make_agent(grok_home)

    # --- collect: scan_sessions then build_usage (tracker) ---
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
    assert isinstance(result.usage, UsageReport)
    assert result.usage.kept_sessions >= 1
    assert isinstance(result.collect_summary, ScanResult)
    assert result.collect_summary.sessions_seen == 1

    # --- phrases: build_phrases from the session records (phrases) ---
    result = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={"traces_action": "phrases", "grok_home": str(grok_home), "run_dir": str(run_dir)},
        )
    )
    assert result.ok
    assert isinstance(result.phrases, PhrasesReport)

    # --- state-set: set the pending run status (state) ---
    got = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={
                "traces_action": "state",
                "grok_home": str(grok_home),
                "run_dir": str(run_dir),
                "state_action": "set",
                "status": "collected",
            },
        )
    )
    assert got.ok
    assert got.state == TraceStateStatus.COLLECTED

    # --- state-get: the pending status is readable ---
    got = agent.execute(
        SkillsRequest(
            op=SkillsOp.TRACES,
            flags={"traces_action": "state", "grok_home": str(grok_home), "state_action": "get"},
        )
    )
    assert got.ok
    assert got.state in (TraceStateStatus.COLLECTED, TraceStateStatus.RUNNING)

    # Protocol conformance (capabilities are the real implementations).
    assert isinstance(agent._scan, ISkillsTraceScanProtocol)


def test_integration_state_wait_maps_to_exit_statuses(tmp_path: Path) -> None:
    """INT-TRACE-002: wait returns distinct TraceStateStatus outcomes."""
    grok_home = make_grok_home(tmp_path, cwd="/home/raka/proj")
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)
    agent = _make_agent(grok_home)

    # report.md + actions.json present → REPORT_READY
    (run_dir / "report.md").write_text("report")
    (run_dir / "actions.json").write_text("{}")
    got = agent.execute(
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
    assert got.ok
    assert got.state_status == TraceStateStatus.REPORT_READY
