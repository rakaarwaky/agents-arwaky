"""Smoke tests for modules/mcp — fast import and basic checks."""
from __future__ import annotations

import time


def test_import_mcp_modules():
    """SM-MCP-001: MCP modules can be imported."""
    from modules.mcp.src import capabilities_mcp_generator
    from modules.mcp.src import agent_mcp_orchestrator
    from modules.mcp.src import root_mcp_container

    assert capabilities_mcp_generator is not None
    assert agent_mcp_orchestrator is not None
    assert root_mcp_container is not None


def test_mcp_generator_init_quick():
    """SM-MCP-002: McpConfigGenerator initialization is quick."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

    start = time.time()
    generator = McpConfigGenerator()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_mcp_orchestrator_init_quick():
    """SM-MCP-003: McpOrchestrator initialization is quick."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator

    start = time.time()
    generator = McpConfigGenerator()
    orch = McpOrchestrator(generator)
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_container_creation_quick():
    """SM-MCP-004: Container creation is quick."""
    from modules.mcp.src.root_mcp_container import McpContainer

    start = time.time()
    container = McpContainer()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Container creation took {elapsed:.2f}s"
