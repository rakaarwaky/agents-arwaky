"""Shared mcp-domain: taxonomy + contracts for MCP config generation."""
from modules.shared.src.mcp.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.mcp.contract_mcp_protocol import IMcpConfigGenerator
from modules.shared.src.mcp.taxonomy_mcp_vo import McpServer

__all__ = ["IMcpAggregate", "IMcpConfigGenerator", "McpServer"]
