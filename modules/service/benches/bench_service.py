"""Benchmarks for modules/service — performance testing."""
from __future__ import annotations


def bench_service_manager_init(benchmark):
    """BENCH-SERVICE-001: Benchmark ServiceManager initialization."""
    from modules.service.src.capabilities_service_manager import ServiceManager

    benchmark(ServiceManager)


def bench_service_orchestrator_init(benchmark):
    """BENCH-SERVICE-002: Benchmark ServiceOrchestrator initialization."""
    from modules.service.src.capabilities_service_manager import ServiceManager
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator

    def _init():
        manager = ServiceManager()
        return ServiceOrchestrator(manager)

    benchmark(_init)


def bench_container_creation(benchmark):
    """BENCH-SERVICE-003: Benchmark ServiceContainer creation."""
    from modules.service.src.root_service_container import ServiceContainer

    benchmark(ServiceContainer)
