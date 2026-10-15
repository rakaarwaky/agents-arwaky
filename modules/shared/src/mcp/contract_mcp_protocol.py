"""MCP-domain protocol contract (capability ABC).

Two seam protocols so the MCP orchestrator coordinates two subsystems:
- ``IMcpListProtocol`` — read-only discovery (list servers, show/probe one)
- ``IMcpWriteProtocol`` — mutation ops (generate config, alias, validate)

Capabilities implement these; the composition root injects them into the
orchestrator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.shared.src.mcp.taxonomy_mcp_vo import (
    ExitCode,
    McpAlias,
    McpServerId,
    McpServerInfos,
)


class IMcpListProtocol(ABC):
    """Capability contract for MCP read-only discovery."""

    @abstractmethod
    def list_servers(self) -> McpServerInfos:
        """Return metadata for every registered MCP-enabled tool."""
        ...

    @abstractmethod
    def show_server(self, server_id: McpServerId | None = None) -> ExitCode:
        """Show the generated config or probe one server's help/schema."""
        ...


class IMcpWriteProtocol(ABC):
    """Capability contract for MCP config mutation ops."""

    @abstractmethod
    def generate(self, output: Path) -> ExitCode:
        """Build the unified MCP client config at *output*; return exit code."""
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
    
    "IMcpListProtocol",
    "IMcpWriteProtocol",
    "McpAlias",
    "McpServerId",
    "McpServerInfos",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ExitCode": ExitCode,
    "McpAlias": McpAlias,
    "McpServerId": McpServerId,
    "McpServerInfos": McpServerInfos,
    "IMcpListProtocol": IMcpListProtocol,
    "IMcpWriteProtocol": IMcpWriteProtocol,
}
