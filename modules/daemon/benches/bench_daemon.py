"""Benchmarks for modules/daemon — performance regression detection."""
from __future__ import annotations


def bench_anytype_manager_init(benchmark):
    """BENCH-DAEMON-001: Benchmark AnytypeDaemonManager initialization."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

    benchmark(AnytypeDaemonManager)


def bench_podman_manager_init(benchmark):
    """BENCH-DAEMON-002: Benchmark NinerouterDaemonManager initialization."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager

    benchmark(NinerouterDaemonManager)


def bench_orchestrator_init(benchmark):
    """BENCH-DAEMON-003: Benchmark DaemonOrchestrator initialization."""
    from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager

    def _init():
        ninerouter = NinerouterDaemonManager()
        anytype = AnytypeDaemonManager()
        return DaemonOrchestrator(ninerouter, anytype)

    benchmark(_init)


def bench_container_creation(benchmark):
    """BENCH-DAEMON-004: Benchmark DaemonContainer creation."""
    from modules.daemon.src.root_daemon_container import DaemonContainer

    benchmark(DaemonContainer)


def bench_create_daemon_feature(benchmark):
    """BENCH-DAEMON-005: Benchmark create_daemon_feature."""
    from modules.daemon.src.root_daemon_container import create_daemon_feature

    benchmark(create_daemon_feature)


def bench_anytype_execute_dispatch(benchmark):
    """BENCH-DAEMON-006: Benchmark AnytypeDaemonManager.execute dispatch."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

    manager = AnytypeDaemonManager()

    def _execute():
        # Quick no-op dispatch - would fail without mocking but benchmarks
        # measure the dispatch path itself
        try:
            manager.execute("help")
        except Exception:
            pass

    benchmark(_execute)


def bench_podman_execute_dispatch(benchmark):
    """BENCH-DAEMON-007: Benchmark NinerouterDaemonManager.execute dispatch."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager

    manager = NinerouterDaemonManager()

    def _execute():
        try:
            manager.execute("help")
        except Exception:
            pass

    benchmark(_execute)


def bench_extract_api_key(benchmark):
    """BENCH-DAEMON-008: Benchmark _extract_api_key."""
    from modules.daemon.src.capabilities_anytype_daemon import _extract_api_key

    sample_output = "Generated API key: ABCdef1234567890xyz_more_text\nDone." * 10

    benchmark(_extract_api_key, sample_output)


def bench_has_podman(benchmark):
    """BENCH-DAEMON-009: Benchmark has_podman check."""
    from modules.daemon.src.capabilities_anytype_daemon import has_podman

    benchmark(has_podman)
