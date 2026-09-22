"""MCP-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_mcp_vo import ExitCode, McpServer, McpServerInfo


class IMcpAggregate(ABC):
    """Aggregate over MCP config listing, inspection and generation."""

    @abstractmethod
    def list_servers(self) -> list[McpServerInfo]:
        """List MCP-enabled tools (id, category, description)."""
        return None

    @abstractmethod
    def show_server(self) -> ExitCode:
        """Print the generated MCP config path and contents; return exit code."""
        return None

    @abstractmethod
    def generate_config(self, output: Path) -> ExitCode:
        """Regenerate the unified MCP config; return exit code."""
        return None

__all__ = ['ExitCode', 'IMcpAggregate', 'McpServer', 'McpServerInfo']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IMcpAggregate": IMcpAggregate,
    "McpServer": McpServer,
    "McpServerInfo": McpServerInfo,
}
