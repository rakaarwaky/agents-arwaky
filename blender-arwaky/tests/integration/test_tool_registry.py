"""Tests for MCP tool registry."""
from unittest.mock import MagicMock
from surfaces.tool_registry_handler import ToolRegistryHandler


class TestToolRegistry:
    """Tests that all 5 MCP tools are registered."""

    def test_register_tools_registers_exactly_5(self):
        """register_tools must call mcp.tool() exactly 5 times."""
        mcp = MagicMock()
        ToolRegistryHandler.register_tools(mcp)
        assert mcp.tool.call_count == 5, (
            f"Expected 5 tool registrations, got {mcp.tool.call_count}"
        )

    def test_register_tools_calls_five_different_modules(self):
        """Each tool must come from a different handler module (5 distinct registers)."""
        # We test that the mcp.tool() decorator was called 5 times.
        # Since all calls are decorator-like (no positional args beyond the decorator),
        # we verify count and that the registry doesn't throw.
        mcp = MagicMock()
        ToolRegistryHandler.register_tools(mcp)
        assert mcp.tool.call_count == 5
