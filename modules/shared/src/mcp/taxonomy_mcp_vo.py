"""MCP-domain value objects for the AES mcp feature."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import NewType

#: Process or command exit code (0 = success, non-zero = failure).
ExitCode = NewType("ExitCode", int)

#: Registered MCP server identifier (manifest ``id``).
McpServerId = NewType("McpServerId", str)

#: Client-config alias written by ``generate_alias``.
McpAlias = NewType("McpAlias", str)

#: Operation token carried by a McpRequest (``generate`` | ``list`` | ``show`` | ``alias`` | ``validate``).
McpOp = NewType("McpOp", str)

#: Tuple of server-info rows returned by ``list_servers``.
McpServerInfos = NewType("McpServerInfos", list)

#: MCP request envelope — single shape the aggregate accepts.
@dataclass(frozen=True)
class McpRequest:
    """One MCP request the surface/root/CLI hands to the aggregate.

    Every consumer verb (list, generate, show, alias, validate) is a value of
    ``op``; the aggregate routes internally to the matching protocol method.
    """
    op: McpOp
    output: Path | None = None
    server_id: McpServerId | None = None
    alias: McpAlias | None = None


#: MCP response envelope returned by ``IMcpAggregate.execute``.
McpResponse = NewType("McpResponse", object)


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


__all__ = [
    "ExitCode",
    "McpAlias",
    "McpOp",
    "McpRequest",
    "McpResponse",
    "McpServer",
    "McpServerId",
    "McpServerInfo",
    "McpServerInfos",
]
