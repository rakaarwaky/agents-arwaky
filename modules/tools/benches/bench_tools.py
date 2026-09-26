"""Benchmarks for modules/tools — performance characteristics."""
from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock


def bench_capability_instantiation():
    """Benchmark: instantiate all capability classes."""
    from modules.tools.src.capabilities_tools_installer import InstallerCapability
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
    from modules.tools.src.capabilities_tools_runner import RunnerCapability

    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        InstallerCapability()
        UpdaterCapability()
        UninstallerCapability()
        RunnerCapability()
    elapsed = time.perf_counter() - start

    print(f"Instantiate 4 capabilities x{iterations}: {elapsed:.4f}s ({elapsed/iterations*1000:.3f}ms each)")
    return elapsed


def bench_orchestrator_creation():
    """Benchmark: create ToolsOrchestrator with empty registry."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        ToolsOrchestrator(registry={})
    elapsed = time.perf_counter() - start

    print(f"Create orchestrator x{iterations}: {elapsed:.4f}s ({elapsed/iterations*1000:.3f}ms each)")
    return elapsed


def bench_orchestrator_with_dependencies():
    """Benchmark: create ToolsOrchestrator with mocked dependencies."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        ToolsOrchestrator(
            registry={"test": MagicMock()},
            installer=MagicMock(),
            updater=MagicMock(),
            uninstaller=MagicMock(),
            runner=MagicMock(),
        )
    elapsed = time.perf_counter() - start

    print(f"Create orchestrator w/deps x{iterations}: {elapsed:.4f}s ({elapsed/iterations*1000:.3f}ms each)")
    return elapsed


def bench_manifest_resolution():
    """Benchmark: resolve tool specs from manifest."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.utility_manifest_reader import load_tools

    tools = load_tools()
    iterations = min(100, len(tools))

    start = time.perf_counter()
    for tool in tools[:iterations]:
        from modules.shared.src.taxonomy_tools_vo import ToolQuery, ToolRequest, ToolsOp
        orch = ToolsOrchestrator(registry={})
        orch.execute(ToolRequest(ToolsOp("resolve"), query=ToolQuery(tool.id)))
    elapsed = time.perf_counter() - start

    print(f"Resolve {iterations} tools: {elapsed:.4f}s ({elapsed/iterations*1000:.3f}ms each)")
    return elapsed


def bench_execute_dispatch():
    """Benchmark: execute() dispatch overhead."""
    from modules.tools.src.capabilities_tools_installer import InstallerCapability
    from modules.shared.src.taxonomy_common_vo import ToolSpec

    iterations = 1000
    registry = {"test": MagicMock()}
    installer = InstallerCapability(registry=registry)
    spec = ToolSpec(
        id="test",
        category="dev",
        binary="test",
        is_mcp=False,
        description="test",
        path="/test",
        alias=None,
        mcp_binary=None,
        runner="",
    )

    start = time.perf_counter()
    for _ in range(iterations):
        installer.execute("install", spec=spec)
    elapsed = time.perf_counter() - start

    print(f"Execute install dispatch x{iterations}: {elapsed:.4f}s ({elapsed/iterations*1000:.3f}ms each)")
    return elapsed


if __name__ == "__main__":
    print("=" * 60)
    print("Tools Module Benchmarks")
    print("=" * 60)
    bench_capability_instantiation()
    bench_orchestrator_creation()
    bench_orchestrator_with_dependencies()
    bench_manifest_resolution()
    bench_execute_dispatch()
    print("=" * 60)
