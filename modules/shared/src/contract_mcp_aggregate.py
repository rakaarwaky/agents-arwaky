"""MCP-domain aggregate contract (agent orchestrator ABC).

Single entry point over the MCP feature: the surface, root, CLI and MCP
call ``execute`` with a request and get a response back. The agent behind
the aggregate routes each ``op`` to the matching capability method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_mcp_vo import McpRequest, McpResponse


class IMcpAggregate(ABC):
    """Single entry point over MCP listing, generation and validation."""

    @abstractmethod
    def execute(self, request: McpRequest) -> McpResponse:
        """Run the request the surface/root/CLI asked for; return the response."""
        ...


__all__ = ["IMcpAggregate", "McpRequest", "McpResponse"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "IMcpAggregate": IMcpAggregate,
    "McpRequest": McpRequest,
    "McpResponse": McpResponse,
}
