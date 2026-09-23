"""MCP-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_mcp_vo import (
    ExitCode,
    McpAlias,
    McpServer,
    McpServerId,
    McpServerInfo,
    McpServerInfos,
)


class IMcpAggregate(ABC):
    """Aggregate over MCP listing, inspection, generation and validation."""

    @abstractmethod
    def list_servers(self) -> McpServerInfos:
        """List MCP-enabled tools (id, category, description) without writing."""
        ...
    @abstractmethod
    def show_server(self, server_id: McpServerId | None = None) -> ExitCode:
        """Probe one server's help/schema, or show the generated config; return exit code."""
        ...
    @abstractmethod
    def generate(self, output: Path) -> ExitCode:
        """Write the unified MCP config to *output* (the only write path); return exit code."""
        ...
    @abstractmethod
    def generate_alias(self, alias: McpAlias, output: Path) -> ExitCode:
        """Write an alias-qualified client config to *output* via the same generator (optional)."""
        ...
    @abstractmethod
    def validate(self, output: Path | None = None) -> ExitCode:
        """Parse the generated config at *output* and report validity (optional)."""
        ...

__all__ = ['ExitCode', 'IMcpAggregate', 'McpAlias', 'McpServer', 'McpServerId', 'McpServerInfo']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IMcpAggregate": IMcpAggregate,
    "McpAlias": McpAlias,
    "McpServer": McpServer,
    "McpServerId": McpServerId,
    "McpServerInfo": McpServerInfo,
}
