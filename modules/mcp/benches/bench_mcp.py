"""Benchmarks for modules/mcp — performance testing."""
from __future__ import annotations


def bench_mcp_generator_init(benchmark):
    """BENCH-MCP-001: Benchmark McpConfigGenerator initialization."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

    benchmark(McpConfigGenerator)


def bench_mcp_orchestrator_init(benchmark):
    """BENCH-MCP-002: Benchmark McpOrchestrator initialization."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator

    def _init():
        generator = McpConfigGenerator()
        return McpOrchestrator(generator)

    benchmark(_init)


def bench_container_creation(benchmark):
    """BENCH-MCP-003: Benchmark McpContainer creation."""
    from modules.mcp.src.root_mcp_container import McpContainer

    benchmark(McpContainer)
