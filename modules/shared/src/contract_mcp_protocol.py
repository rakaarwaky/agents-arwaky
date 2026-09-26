"""MCP-domain protocol contract (capability ABC).

Pure capability ABC: one abstract method per MCP operation the generator
exposes. Consumers never see this method list — the aggregate dispatches to
it via its single ``execute`` entry point.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.taxonomy_mcp_vo import (
    ExitCode,
    McpAlias,
    McpServerId,
    McpServerInfos,
)


class IMcpProtocol(ABC):
    """Capability contract for the MCP config generator: one method per op."""

    @abstractmethod
    def generate(self, output: Path) -> ExitCode:
        """Build the unified MCP client config at *output*; return exit code."""
        ...

    @abstractmethod
    def list_servers(self) -> McpServerInfos:
        """Return metadata for every registered MCP-enabled tool."""
        ...

    @abstractmethod
    def show_server(self, server_id: McpServerId | None = None) -> ExitCode:
        """Show the generated config or probe one server's help/schema."""
        ...

    @abstractmethod
    def generate_alias(self, alias: McpAlias, output: Path) -> ExitCode:
        """Write an alias-qualified client config via the same generator."""
        ...

    @abstractmethod
    def validate(self, output: Path | None = None) -> ExitCode:
        """Parse the generated config at *output* and report validity."""
        ...


__all__ = [
    "ExitCode",
    "IMcpProtocol",
    "McpAlias",
    "McpServerId",
    "McpServerInfos",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "IMcpProtocol": IMcpProtocol,
    "McpAlias": McpAlias,
    "McpServerId": McpServerId,
    "McpServerInfos": McpServerInfos,
}
