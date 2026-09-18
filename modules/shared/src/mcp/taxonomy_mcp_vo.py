"""MCP-domain value objects for the AES mcp feature."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class McpServer:
    """One generated MCP server entry."""

    name: str
    command: str
    args: tuple[str, ...] = ()
    env: tuple[tuple[str, str], ...] = ()
