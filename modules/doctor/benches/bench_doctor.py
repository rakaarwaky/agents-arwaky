"""Benchmarks for modules/doctor — performance testing."""
from __future__ import annotations


def bench_env_runner_init(benchmark):
    """BENCH-DOCTOR-001: Benchmark EnvDiagnosticRunner initialization."""
    from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner

    benchmark(EnvDiagnosticRunner)


def bench_tools_runner_init(benchmark):
    """BENCH-DOCTOR-002: Benchmark ToolsDiagnosticRunner initialization."""
    from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

    benchmark(ToolsDiagnosticRunner)
