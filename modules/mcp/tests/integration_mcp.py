"""Integration tests for modules/mcp — test component interactions."""
from __future__ import annotations

from pathlib import Path
import tempfile


def test_mcp_generator_list_servers():
    """IT-MCP-001: list_servers returns valid MCP server info."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

    generator = McpConfigGenerator()
    servers = generator.list_servers()
    assert isinstance(servers, list)


def test_mcp_orchestrator_creation():
    """IT-MCP-002: McpOrchestrator can be created with generator."""
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

    generator = McpConfigGenerator()
    orch = McpOrchestrator(generator)
    assert orch is not None


def test_mcp_container_creation():
    """IT-MCP-003: McpContainer creates valid aggregate."""
    from modules.mcp.src.root_mcp_container import McpContainer

    container = McpContainer()
    aggregate = container.aggregate
    assert aggregate is not None


def test_mcp_generate_output():
    """IT-MCP-004: generate creates valid JSON output."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

    generator = McpConfigGenerator()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        path = Path(f.name)
    try:
        generator.generate(path)
        content = path.read_text(encoding='utf-8')
        assert 'mcpServers' in content
    finally:
        path.unlink(missing_ok=True)
