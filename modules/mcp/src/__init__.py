"""MCP feature — public symbols.

Re-exports the orchestrator, container, and surface entry points so
feature consumers can import from ``modules.mcp`` directly.
"""
from __future__ import annotations

from modules.mcp.src.agent_mcp_orchestrator import McpOrchestrator
from modules.mcp.src.capabilities_mcp_generator import McpConfigGenerator
from modules.mcp.src.root_mcp_container import McpContainer, create_mcp_feature
from modules.cli.src.surface_mcp_command import cmd_mcp

__all__ = [
    "McpConfigGenerator",
    "McpContainer",
    "McpOrchestrator",
    "cmd_mcp",
    "create_mcp_feature",
]
