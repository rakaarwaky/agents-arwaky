"""MCP config generator capability — port of tools/mcp/generate_config.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from modules.shared.src.common.taxonomy_core_constant import ANYTYPE_BASE_URL
from modules.shared.src.envfile.utility_envfile import load_first_env
from modules.shared.src.mcp.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.mcp.contract_mcp_protocol import IMcpConfigGenerator
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.xdg.utility_xdg_paths import agents_arwaky_config_dir, config_home


class McpConfigGenerator(IMcpConfigGenerator, IMcpAggregate):
    """Read the manifest + env files and write mcp_servers.generated.json.

    # Block 1: Constructor & env resolution
    # Block 2: Config assembly & generation
    # Block 3: Aggregate inspection verbs (list/show)
    """

    # -- Block 1: Constructor & env resolution -----------------------------------
    def __init__(self) -> None:
        self._root = repo_root()

    def _load_anytype_env(self) -> tuple[str, str]:
        env = load_first_env([
            agents_arwaky_config_dir() / "anytype.env",
            config_home() / "anytype-mcp/.env",
            self._root / "tools/config/anytype.env",
            self._root / ".env",
        ])
        base_url = env.get("ANYTYPE_API_BASE_URL", ANYTYPE_BASE_URL)
        api_key = env.get("ANYTYPE_API_KEY", "<YOUR_API_KEY>")
        if not api_key or api_key in ("<YOUR_API_KEY>", "change-me", "<YOUR_ANYTYPE_API_KEY>", ""):
            print("  \u26a0 Warning: ANYTYPE_API_KEY is not set or is a placeholder.", file=sys.stderr)
            print("    Run 'aa anytype auth-key' to generate a valid key.", file=sys.stderr)
            api_key = "<YOUR_API_KEY>"
        return base_url, api_key

    # -- Block 2: Config assembly & generation ------------------------------------
    def generate(self, output: Path) -> int:
        """Write the unified MCP client config to *output*; returns 0."""
        print("Generating unified MCP client configuration...")
        print(f"Target: {output}")
        anytype_base, anytype_key = self._load_anytype_env()
        manifest_path = self._root / "tools/config/manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        config: dict = {"mcpServers": {}}
        for tool in manifest.get("tools", []):
            if not tool.get("isMcp", False):
                continue
            tool_id = tool["id"]
            binary = tool.get("mcpBinary") or tool["binary"]
            entry: dict = {"command": binary}
            if tool.get("mcpArgs"):
                entry["args"] = list(tool["mcpArgs"])
            if tool_id == "anytype":
                entry["env"] = {
                    "ANYTYPE_API_BASE_URL": anytype_base,
                    "OPENAPI_MCP_HEADERS": json.dumps(
                        {"Authorization": f"Bearer {anytype_key}", "Anytype-Version": "2025-11-08"},
                        ensure_ascii=False,
                    ),
                }
            config["mcpServers"][tool_id] = entry
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            output.chmod(0o600)
        except OSError:
            print("Warning: could not set 0600 permissions on generated MCP config.", file=sys.stderr)
        print(f"Generated valid JSON configuration at {output}")
        return 0

    # -- Block 3: Aggregate inspection verbs ---------------------------------------
    def list_servers(self) -> list[dict[str, object]]:
        """MCP-enabled tools from the manifest."""
        from modules.shared.src.manifest.capabilities_manifest_reader import load_tools

        return [
            {"id": tool.id, "category": tool.category, "description": tool.description}
            for tool in load_tools()
            if tool.is_mcp
        ]

    def show_server(self) -> int:
        generated = self._root / "mcp_servers.generated.json"
        if not generated.exists():
            print("Configuration file not found. Generating now...")
            self.generate(generated)
        if generated.exists():
            print(f"Path: {generated}")
            print()
            print(generated.read_text(encoding="utf-8"))
            return 0
        print("Failed to generate MCP configuration.", file=sys.stderr)
        return 1

    def generate_config(self, output: Path) -> int:
        return self.generate(output)
