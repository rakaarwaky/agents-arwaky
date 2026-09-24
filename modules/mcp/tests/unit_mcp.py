"""Unit tests for modules/mcp — test individual functions and methods."""
from __future__ import annotations

from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch


class TestMcpConfigGenerator:
    """Tests for McpConfigGenerator class."""

    def test_init_creates_generator(self):
        """UT-MCP-001: McpConfigGenerator initializes correctly."""
        from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

        generator = McpConfigGenerator()
        assert generator is not None
        assert generator._root is not None

    def test_execute_method_exists(self):
        """UT-MCP-002: execute method exists."""
        from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

        generator = McpConfigGenerator()
        assert hasattr(generator, 'execute')
        assert callable(getattr(generator, 'execute'))

    def test_list_servers_method_exists(self):
        """UT-MCP-003: list_servers method exists."""
        from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

        generator = McpConfigGenerator()
        assert hasattr(generator, 'list_servers')
        assert callable(getattr(generator, 'list_servers'))

    def test_generate_method_exists(self):
        """UT-MCP-004: generate method exists."""
        from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

        generator = McpConfigGenerator()
        assert hasattr(generator, 'generate')
        assert callable(getattr(generator, 'generate'))

    def test_validate_method_exists(self):
        """UT-MCP-005: validate method exists."""
        from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

        generator = McpConfigGenerator()
        assert hasattr(generator, 'validate')
        assert callable(getattr(generator, 'validate'))

    def test_show_server_method_exists(self):
        """UT-MCP-006: show_server method exists."""
        from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

        generator = McpConfigGenerator()
        assert hasattr(generator, 'show_server')
        assert callable(getattr(generator, 'show_server'))


class TestMcpOrchestrator:
    """Tests for McpOrchestrator class."""

    def test_init_creates_orchestrator(self):
        """UT-MCP-007: McpOrchestrator initializes correctly."""
        from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
        from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

        generator = McpConfigGenerator()
        orch = McpOrchestrator(generator)
        assert orch is not None

    def test_list_servers_delegates(self):
        """UT-MCP-008: list_servers delegates to generator."""
        from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
        from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

        generator = McpConfigGenerator()
        orch = McpOrchestrator(generator)
        result = orch.list_servers()
        assert isinstance(result, list)

    def test_generate_method_delegates(self):
        """UT-MCP-009: generate delegates to generator."""
        from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
        from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator

        generator = McpConfigGenerator()
        orch = McpOrchestrator(generator)
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = Path(f.name)
        try:
            orch.generate(path)
            assert path.exists()
        finally:
            path.unlink(missing_ok=True)
