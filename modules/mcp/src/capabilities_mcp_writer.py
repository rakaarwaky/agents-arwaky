"""MCP config writer capability (AES capabilities layer).

``McpConfigWriter`` implements ``IMcpWriteProtocol`` (mutation ops:
generate, alias, validate).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from modules.shared.src.mcp.contract_mcp_protocol import IMcpWriteProtocol
from modules.shared.src.mcp.taxonomy_mcp_vo import (
    ExitCode,
    McpAlias,
)
from modules.shared.src.taxonomy_common_vo import config_home
from modules.shared.src.utility_envfile_parser import load_first_env
from modules.shared.src.utility_mcp_manifest import load_mcp_manifest
from modules.shared.src.utility_paths_resolver import repo_root

__all__ = ["McpConfigWriter"]

# ─── Block 1: Class Definition & Constructor ──────────────
class McpConfigWriter(IMcpWriteProtocol):
    """Write the unified MCP client config and aliases."""

    def __init__(self) -> None:
        self._root = repo_root()

    # ─── Block 2: Protocol Method Implementation ──────────────
    def generate(self, output: Path) -> ExitCode:
        """Write the unified MCP client config to *output*; return exit code."""
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
        target = output or self._root / "mcp_servers.generated.json"
        if not target.is_file():
            return ExitCode(1)
        try:
            json.loads(target.read_text())
            return ExitCode(0)
        except (json.JSONDecodeError, OSError):
            return ExitCode(1)

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────────
    def _main(self) -> int:
        """Original generate_config.py body — kept as-is."""
        manifest = load_mcp_manifest(self._root)
        servers: dict = {}
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
        output_path = (
            Path(sys.argv[1]) if len(sys.argv) > 1
            else self._root / "mcp_servers.generated.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"mcpServers": servers}, indent=2))
        return 0

    def __repr__(self) -> str:
        return "McpConfigWriter()"
