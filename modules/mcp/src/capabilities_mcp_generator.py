"""MCP capabilities (AES capabilities layer).

Two capabilities, one per contract seam:
- ``McpConfigLister`` implements ``IMcpListProtocol`` (read-only discovery)
- ``McpConfigWriter`` implements ``IMcpWriteProtocol`` (mutation)

Both are thin wrappers around the original ``McpConfigGenerator`` body.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from modules.shared.src.mcp.contract_mcp_protocol import (
    IMcpListProtocol,
    IMcpWriteProtocol,
)
from modules.shared.src.mcp.taxonomy_mcp_vo import (
    ExitCode,
    McpAlias,
    McpServerId,
    McpServerInfo,
    McpServerInfos,
)
from modules.shared.src.taxonomy_common_vo import (
    config_home,
)
from modules.shared.src.utility_envfile_parser import load_first_env
from modules.shared.src.utility_paths_resolver import repo_root

__all__ = [
    "McpConfigGenerator",
    "McpConfigLister",
    "McpConfigWriter",
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


class McpConfigWriter(IMcpWriteProtocol):
    """Write the unified MCP client config and aliases."""

    def __init__(self) -> None:
        self._root = repo_root()

    # ─── Block 2: Protocol Method Implementation ──────────────
    def generate(self, output: Path) -> ExitCode:
        """Write the unified MCP client config to *output*; return exit code.

        Delegates to the unchanged original ``main()`` body, passing
        *output* as the explicit target (the original honours
        ``sys.argv[1]`` exactly this way).
        """
        original_argv = list(sys.argv)
        sys.argv = [sys.argv[0], str(output)]
        try:
            return ExitCode(self._main())
        finally:
            sys.argv = original_argv

    def generate_alias(self, alias: McpAlias, output: Path) -> ExitCode:
        """Write an alias-qualified client config via the same generator."""
        original_argv = list(sys.argv)
        sys.argv = [sys.argv[0], "--alias", str(alias), str(output)]
        try:
            return ExitCode(self._main())
        finally:
            sys.argv = original_argv

    def validate(self, output: Path | None = None) -> ExitCode:
        """Parse the generated config at *output* and report validity."""
        import json
        target = output or self._root / "mcp_servers.generated.json"
        if not target.is_file():
            return ExitCode(1)
        try:
            json.loads(target.read_text())
            return ExitCode(0)
        except (json.JSONDecodeError, OSError):
            return ExitCode(1)

    def _main(self) -> int:
        """Original generate_config.py body — kept as-is."""
        manifest = _load_manifest(self._root)
        servers = {}
        for tool_id, tool in manifest.items():
            if not tool.get("mcp"):
                continue
            env_name = tool.get("env") or tool_id
            env_path = config_home() / f".{env_name}.env"
            env = load_first_env(env_path)
            cmd = tool.get("command", tool_id)
            args = tool.get("args", [])
            if env:
                env_str = " ".join(f"{k}={v}" for k, v in env.items())
                cmd = f"{env_str} {cmd}"
            servers[tool_id] = {"command": cmd, "args": args}
        output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else self._root / "mcp_servers.generated.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"mcpServers": servers}, indent=2))
        return 0

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def __repr__(self) -> str:
        return "McpConfigWriter()"