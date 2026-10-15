"""Contract tests for modules/mcp — verify protocol implementations."""
from __future__ import annotations


def test_mcp_protocol_exists():
    """CP-MCP-001: IMcpProtocol exists and can be imported."""
    from modules.shared.src.mcp.contract_mcp_protocol import (
        IMcpListProtocol,
        IMcpWriteProtocol,
    )

    assert IMcpListProtocol is not None
    assert IMcpWriteProtocol is not None


def test_mcp_generator_exists():
    """CP-MCP-002: McpConfigLister class exists."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigLister
    from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter

    assert McpConfigLister is not None
    assert McpConfigWriter is not None


def test_mcp_orchestrator_exists():
    """CP-MCP-003: McpOrchestrator class exists."""
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator

    assert McpOrchestrator is not None


def test_mcp_generator_implements_protocol():
    """CP-MCP-004: McpConfigLister/McpConfigWriter implement the protocols."""
    from modules.mcp.src.capabilities_mcp_generator import McpConfigLister
    from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter
    from modules.shared.src.mcp.contract_mcp_protocol import (
        IMcpListProtocol,
        IMcpWriteProtocol,
    )

    lister = McpConfigLister()
    writer = McpConfigWriter()
    assert isinstance(lister, IMcpListProtocol)
    assert isinstance(writer, IMcpWriteProtocol)


def test_mcp_orchestrator_implements_aggregate():
    """CP-MCP-005: McpOrchestrator implements IMcpAggregate."""
    from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
    from modules.mcp.src.capabilities_mcp_generator import McpConfigLister
    from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter
    from modules.shared.src.mcp.contract_mcp_aggregate import IMcpAggregate

    lister = McpConfigLister()
    writer = McpConfigWriter()
    orch = McpOrchestrator(lister, writer)
    assert isinstance(orch, IMcpAggregate)

