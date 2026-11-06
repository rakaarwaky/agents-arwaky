"""Benchmarks for skills/skill-authoring/skill-traces/modules/skills_traces — performance testing."""
from __future__ import annotations


def bench_scan_init(benchmark):
    """BENCH-TRACE-001: Benchmark SkillsTracesScan initialization."""
    from skills_traces.src.capabilities_skills_scan import SkillsTracesScan

    benchmark(SkillsTracesScan)


def bench_state_init(benchmark):
    """BENCH-TRACE-002: Benchmark SkillsTracesState initialization."""
    from skills_traces.src.capabilities_skills_state import SkillsTracesState

    benchmark(SkillsTracesState)


def bench_agent_init(benchmark):
    """BENCH-TRACE-003: Benchmark SkillsAgent initialization."""
    from skills_traces.src.agent_skills_orchestrator import SkillsAgent
    from skills_traces.src.capabilities_skills_scan import SkillsTracesScan
    from skills_traces.src.capabilities_skills_state import SkillsTracesState

    agent = SkillsAgent(scan=SkillsTracesScan(), state=SkillsTracesState())
    benchmark(lambda: agent)
