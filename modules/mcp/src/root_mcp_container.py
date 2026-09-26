"""MCP composition root — wires the generator into the orchestrator."""
from __future__ import annotations

from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator
from modules.shared.src.contract_mcp_aggregate import IMcpAggregate


class McpContainer:
    """Construct the generator and the orchestrator."""

    def __init__(self) -> None:
        generator = McpConfigGenerator()
        self._orchestrator = McpOrchestrator(generator)

    @property
    def aggregate(self) -> IMcpAggregate:
        """Expose the MCP orchestrator as the feature's public aggregate."""
        return self._orchestrator


def create_mcp_feature() -> IMcpAggregate:
    """Fully-wired mcp feature aggregate."""
    return McpContainer().aggregate
