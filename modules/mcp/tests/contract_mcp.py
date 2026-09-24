"""Contract tests for modules/mcp — verify protocol implementations."""
from __future__ import annotations


def test_mcp_protocol_exists():
    """CP-MCP-001: IMcpProtocol exists and can be imported."""
    from modules.shared.src.contract_mcp_protocol import IMcpProtocol

    assert IMcpProtocol is not None


def test_mcp_generator_exists():
    """CP-MCP-002: McpConfigGenerator class exists."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

    assert McpConfigGenerator is not None


def test_mcp_orchestrator_exists():
    """CP-MCP-003: McpOrchestrator class exists."""
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator

    assert McpOrchestrator is not None


def test_mcp_generator_implements_protocol():
    """CP-MCP-004: McpConfigGenerator implements IMcpProtocol."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator
    from modules.shared.src.contract_mcp_protocol import IMcpProtocol

    generator = McpConfigGenerator()
    assert isinstance(generator, IMcpProtocol)


def test_mcp_orchestrator_implements_aggregate():
    """CP-MCP-005: McpOrchestrator implements IMcpAggregate."""
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
    from modules.shared.src.contract_mcp_aggregate import IMcpAggregate
    from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

    generator = McpConfigGenerator()
    orchestrator = McpOrchestrator(generator)
    assert isinstance(orchestrator, IMcpAggregate)
