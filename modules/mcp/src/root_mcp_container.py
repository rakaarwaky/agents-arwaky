"""MCP composition root — wires the lister/writer into the orchestrator."""
from __future__ import annotations

from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
from modules.mcp.src.capabilities_mcp_generator import McpConfigLister
from modules.mcp.src.capabilities_mcp_writer import McpConfigWriter
from modules.shared.src.mcp.contract_mcp_aggregate import IMcpAggregate


class McpContainer:
    """Construct the lister, writer, and the orchestrator."""

    def __init__(self) -> None:
        lister = McpConfigLister()
        writer = McpConfigWriter()
        self._orchestrator = McpOrchestrator(list_cap=lister, write_cap=writer)

    @property
    def aggregate(self) -> IMcpAggregate:
        """Expose the MCP orchestrator as the feature's public aggregate."""
        return self._orchestrator


def create_mcp_feature() -> IMcpAggregate:
    """Fully-wired mcp feature aggregate."""
    return McpContainer().aggregate