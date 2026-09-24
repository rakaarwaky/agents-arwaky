"""Benchmarks for modules/check — performance testing."""
from __future__ import annotations


def bench_docs_runner_init(benchmark):
    """BENCH-CHECK-001: Benchmark DocsCheckRunner initialization."""
    from modules.check.src.capabilities_check_docs import DocsCheckRunner

    benchmark(DocsCheckRunner)


def bench_skills_runner_init(benchmark):
    """BENCH-CHECK-002: Benchmark SkillsCheckRunner initialization."""
    from modules.check.src.capabilities_check_skills import SkillsCheckRunner

    benchmark(SkillsCheckRunner)


def bench_orchestrator_init(benchmark):
    """BENCH-CHECK-003: Benchmark CheckOrchestrator initialization."""
    from modules.check.src.agent_check_orchestrator import CheckOrchestrator
    from modules.check.src.capabilities_check_docs import DocsCheckRunner

    def _init():
        return CheckOrchestrator([DocsCheckRunner()])

    benchmark(_init)
