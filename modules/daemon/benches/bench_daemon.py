"""Benchmarks for modules/daemon — performance regression detection."""
from __future__ import annotations


def bench_podman_manager_init(benchmark):
    """BENCH-DAEMON-002: Benchmark OmnirouteDaemonManager initialization."""
    from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager

    benchmark(OmnirouteDaemonManager)


def bench_orchestrator_init(benchmark):
    """BENCH-DAEMON-003: Benchmark DaemonOrchestrator initialization."""
    from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
    from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager

    def _init():
        omniroute = OmnirouteDaemonManager()
        return DaemonOrchestrator(omniroute)

    benchmark(_init)


def bench_container_creation(benchmark):
    """BENCH-DAEMON-004: Benchmark DaemonContainer creation."""
    from modules.daemon.src.root_daemon_container import DaemonContainer

    benchmark(DaemonContainer)


def bench_create_daemon_feature(benchmark):
    """BENCH-DAEMON-005: Benchmark create_daemon_feature."""
    from modules.daemon.src.root_daemon_container import create_daemon_feature

    benchmark(create_daemon_feature)


def bench_podman_execute_dispatch(benchmark):
    """BENCH-DAEMON-007: Benchmark OmnirouteDaemonManager.execute dispatch."""
    from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager

    manager = OmnirouteDaemonManager()

    def _execute():
        try:
            manager.execute("help")
        except Exception:  # noqa: BLE001,S110
            pass

    benchmark(_execute)
