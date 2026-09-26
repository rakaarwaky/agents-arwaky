"""Benchmarks for modules/harness — performance testing."""
from __future__ import annotations


def bench_harness_connector_init(benchmark):
    """BENCH-HARNESS-001: Benchmark HarnessConnector initialization."""
    from modules.harness.src.capabilities_harness_connector import HarnessConnector

    benchmark(HarnessConnector, {})


def bench_harness_disconnector_init(benchmark):
    """BENCH-HARNESS-002: Benchmark HarnessDisconnector initialization."""
    from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector

    benchmark(HarnessDisconnector)


def bench_harness_skills_init(benchmark):
    """BENCH-HARNESS-003: Benchmark HarnessSkills initialization."""
    from modules.harness.src.capabilities_harness_skills import HarnessSkills

    benchmark(HarnessSkills)


def bench_container_creation(benchmark):
    """BENCH-HARNESS-004: Benchmark HarnessContainer creation."""
    from modules.harness.src.root_harness_container import HarnessContainer

    benchmark(HarnessContainer)
