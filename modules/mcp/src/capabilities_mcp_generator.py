"""MCP capabilities (AES capabilities layer).

Two capabilities, one per contract seam:
- ``McpConfigLister`` implements ``IMcpListProtocol`` (read-only discovery)
- ``McpConfigWriter`` implements ``IMcpWriteProtocol`` (mutation)

Both are thin wrappers around the original ``McpConfigGenerator`` body.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from modules.shared.src.mcp.contract_mcp_protocol import IMcpListProtocol
from modules.shared.src.mcp.taxonomy_mcp_vo import (
    ExitCode,
    McpServerId,
    McpServerInfo,
    McpServerInfos,
)
from modules.shared.src.taxonomy_common_vo import (
    config_home,
)
from modules.shared.src.utility_paths_resolver import repo_root

__all__ = [
    "McpConfigLister",
]

# ─── Internal helpers ────────────────────────────────────────
def _load_manifest(root: Path) -> dict:
    """Read the MCP manifest."""
    manifest_path = root / "tools" / "mcp" / "manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        return json.loads(manifest_path.read_text())
    except json.JSONDecodeError:
        return {}


# ─── Block 1: Class Definition & Constructor ──────────────
class McpConfigLister(IMcpListProtocol):
    """Read the manifest + env files for read-only discovery."""

    def __init__(self) -> None:
        self._root = repo_root()

    # ─── Block 2: Protocol Method Implementation ──────────────
    def list_servers(self) -> McpServerInfos:
        """MCP-enabled tools from the manifest (read-only)."""
        manifest = _load_manifest(self._root)
        infos = []
        for tool_id, tool in manifest.items():
            if tool.get("mcp"):
                env_name = tool.get("env") or tool_id
                env_path = config_home() / f".{env_name}.env"
                has_env = env_path.is_file()
                infos.append(
                    McpServerInfo(
                        id=tool_id,
                        name=tool.get("name", tool_id),
                        has_env=has_env,
                        requires_auth=tool.get("auth", False),
                    )
                )
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
