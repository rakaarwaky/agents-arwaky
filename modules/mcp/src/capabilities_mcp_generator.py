"""MCP capabilities (AES capabilities layer).

Two capabilities, one per contract seam:
- ``McpConfigLister`` implements ``IMcpListProtocol`` (read-only discovery)
- ``McpConfigWriter`` implements ``IMcpWriteProtocol`` (mutation)

Both are thin wrappers around the original ``McpConfigGenerator`` body.
The manifest-reading helper is shared via ``utility_mcp_manifest`` so
neither capability imports the other.
"""
from __future__ import annotations

import subprocess

from modules.shared.src.common.utility_mcp_manifest import load_mcp_manifest
from modules.shared.src.common.utility_paths_resolver import repo_root
from modules.shared.src.mcp.contract_mcp_protocol import IMcpListProtocol
from modules.shared.src.mcp.taxonomy_mcp_vo import (
    ExitCode,
    McpServerId,
    McpServerInfo,
    McpServerInfos,
)

__all__ = [
    "McpConfigLister",
]


# ─── Block 1: Class Definition & Constructor ──────────────
class McpConfigLister(IMcpListProtocol):
    """Read the manifest + env files for read-only discovery."""

    def __init__(self) -> None:
        self._root = repo_root()

    # ─── Block 2: Protocol Method Implementation ──────────────
    def list_servers(self) -> McpServerInfos:
        """MCP-enabled tools from the manifest (read-only)."""
        manifest = load_mcp_manifest(self._root)
        infos = [
            McpServerInfo(
                id=tool_id,
                category=str(tool.get("category", "")),
                description=str(tool.get("description", "")),
            )
            for tool_id, tool in manifest.items()
            if tool.get("mcp")
        ]
        return McpServerInfos(tuple(infos))

    def show_server(self, server_id: McpServerId | None = None) -> ExitCode:
        """Show the generated config or probe one server's help/schema."""
        if server_id is None:
            return ExitCode(1)
        cmd = ["mcp", "generate", str(server_id), "--dry-run"]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return ExitCode(0)
        except subprocess.CalledProcessError:
            return ExitCode(1)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "McpConfigLister()"
