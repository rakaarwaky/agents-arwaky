"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_mcp_pipeline():
    """DOG-MCP-001: Basic dogfood check for mcp module."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator

    generator = McpConfigGenerator()
    orch = McpOrchestrator(generator)

    assert hasattr(generator, 'generate')
    assert hasattr(orch, 'execute')
