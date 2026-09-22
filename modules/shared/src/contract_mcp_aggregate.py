"""MCP-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations
from modules.mcp.src.taxonomy_mcp_vo import McpServer


from abc import ABC, abstractmethod
from pathlib import Path


class IMcpAggregate(ABC):
    """Aggregate over MCP config listing, inspection and generation."""

    @abstractmethod
    def list_servers(self) -> list[dict[str, object]]:
        """List MCP-enabled tools (id, category, description)."""
        return None

    @abstractmethod
    def show_server(self) -> int:
        """Print the generated MCP config path and contents; return exit code."""
        return None

    @abstractmethod
    def generate_config(self, output: Path) -> int:
        """Regenerate the unified MCP config; return exit code."""
        return None

__all__ = ['McpServer']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"McpServer": McpServer}
