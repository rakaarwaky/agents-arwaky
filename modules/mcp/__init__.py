"""MCP feature package — MCP config generation (mcp_servers.generated.json).

Public re-exports: orchestrator + container.
"""
from __future__ import annotations

from modules.mcp.src import (
    McpContainer,
    McpOrchestrator,
    create_mcp_feature,
)

__all__ = [
    "McpContainer",
    "McpOrchestrator",
    "create_mcp_feature",
]
