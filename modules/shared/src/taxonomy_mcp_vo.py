"""MCP-domain value objects for the AES mcp feature."""
from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

#: Process or command exit code (0 = success, non-zero = failure).
ExitCode = NewType("ExitCode", int)

#: Registered MCP server identifier (manifest ``id``).
McpServerId = NewType("McpServerId", str)

#: Client-config alias written by ``generate_alias``.
McpAlias = NewType("McpAlias", str)

#: Operation token dispatched through ``IMcpProtocol.execute``.
McpOp = NewType("McpOp", str)

#: Tuple of server-info rows returned by ``IMcpAggregate.list_servers``.
McpServerInfos = NewType("McpServerInfos", list)


@dataclass(frozen=True)
class McpServer:
    """One generated MCP server entry."""

    name: str
    command: str
    args: tuple[str, ...] = ()
    env: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class McpServerInfo:
    """Summary row from ``aa mcp list``: id, category, description."""

    id: str
    category: str
    description: str


__all__ = ["ExitCode", "McpAlias", "McpOp", "McpServer", "McpServerId", "McpServerInfo", "McpServerInfos"]
