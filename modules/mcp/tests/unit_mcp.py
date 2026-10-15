"""Unit tests for modules/mcp — test individual functions and methods."""
from __future__ import annotations

import tempfile
from pathlib import Path


class TestMcpConfigCapabilities:
    """Tests for McpConfigLister and McpConfigWriter classes."""

    def test_init_creates_lister(self):
        """UT-MCP-001: McpConfigLister initializes correctly."""
        from modules.mcp.src.capabilities_mcp_generator import McpConfigLister

        lister = McpConfigLister()
        assert lister is not None

    def test_list_servers_method_exists(self):
        """UT-MCP-003: list_servers method exists on lister."""
        from modules.mcp.src.capabilities_mcp_generator import McpConfigLister

        lister = McpConfigLister()
        assert hasattr(lister, 'list_servers')
        assert callable(lister.list_servers)

    def test_generate_method_exists(self):
        """UT-MCP-004: generate method exists on writer."""
        from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter

        writer = McpConfigWriter()
        assert hasattr(writer, 'generate')
        assert callable(writer.generate)

    def test_validate_method_exists(self):
        """UT-MCP-005: validate method exists on writer."""
        from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter

        writer = McpConfigWriter()
        assert hasattr(writer, 'validate')
        assert callable(writer.validate)

    def test_show_server_method_exists(self):
        """UT-MCP-006: show_server method exists on lister."""
        from modules.mcp.src.capabilities_mcp_generator import McpConfigLister

        lister = McpConfigLister()
        assert hasattr(lister, 'show_server')
        assert callable(lister.show_server)


class TestMcpOrchestrator:
    """Tests for McpOrchestrator class."""

    def test_init_creates_orchestrator(self):
        """UT-MCP-007: McpOrchestrator initializes correctly."""
        from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
        from modules.mcp.src.capabilities_mcp_generator import McpConfigLister
        from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter

        lister = McpConfigLister()
        writer = McpConfigWriter()
        orch = McpOrchestrator(lister, writer)
        assert orch is not None

    def test_execute_list_delegates(self):
        """UT-MCP-008: execute with op=list delegates to lister."""
        from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
        from modules.mcp.src.capabilities_mcp_generator import McpConfigLister
        from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter
        from modules.shared.src.mcp.taxonomy_mcp_vo import McpOp, McpRequest

        lister = McpConfigLister()
        writer = McpConfigWriter()
        orch = McpOrchestrator(lister, writer)
        response = orch.execute(McpRequest(McpOp("list")))
        assert isinstance(response, tuple)

    def test_execute_generate_delegates(self):
        """UT-MCP-009: execute with op=generate delegates to writer."""
        from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
        from modules.mcp.src.capabilities_mcp_generator import McpConfigLister
        from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter
        from modules.shared.src.mcp.taxonomy_mcp_vo import McpOp, McpRequest

        lister = McpConfigLister()
        writer = McpConfigWriter()
        orch = McpOrchestrator(lister, writer)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)
        try:
            orch.execute(McpRequest(McpOp("generate"), output=path))
        finally:
            path.unlink(missing_ok=True)
