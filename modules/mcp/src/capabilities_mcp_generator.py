"""MCP config generator — VERBATIM port of tools/mcp/generate_config.py.

The entire original ``main()`` body (env-file resolution via
``load_first_env``, anytype API-key warning, manifest-driven server
entry construction, atomic write + chmod 0600, and every print /
comment / edge case) is kept exactly as written, with only the
import paths swapped to the AES shared modules. The original module
has no separate ``list_servers`` / ``show_server`` / ``generate_config``
methods — it exposes a single ``main()`` function — so the
``IMcpConfigGenerator`` / ``IMcpAggregate`` contracts expected by the
AES orchestrator (``generate(output)``, ``list_servers()``,
``show_server()``, ``generate_config(output)``) are adapted around
that verbatim body: ``generate`` executes it directly (the original
``main`` already honours ``sys.argv[1]`` as an explicit target and
otherwise defaults to ``ROOT / "mcp_servers.generated.json"``),
``list_servers`` / ``show_server`` reuse the original manifest-driven
listing/inspection behaviour with their original print statements,
and ``generate_config`` delegates to ``generate``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from modules.shared.src.utility_envfile_parser import load_first_env
from modules.mcp.src.contract_mcp_aggregate import IMcpAggregate
from modules.mcp.src.contract_mcp_protocol import IMcpConfigGenerator
from modules.shared.src.utility_paths_resolver import repo_root
from modules.shared.src.taxonomy_xdg_paths import (
    agents_arwaky_config_dir,
    config_home,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class McpConfigGenerator(IMcpConfigGenerator, IMcpAggregate):
    """Read the manifest + env files and write mcp_servers.generated.json.

    # Block 1: Constructor & env resolution
    # Block 2: Config assembly & generation
    # Block 3: Aggregate inspection verbs (list/show)
    """

    # -- Block 1: Constructor & env resolution -----------------------------------
    # ─── Block 2: Protocol ABC Method Implementation ──────────
    def __init__(self) -> None:
        self._root = repo_root()

    # -- Block 2: Config assembly & generation ------------------------------------
    # ─── Block 3: Dunder Methods, Factories & Helpers ───────
    def generate(self, output: Path) -> int:
        """Write the unified MCP client config to *output*; returns 0.

        Delegates to the verbatim original ``main()`` above, passing
        *output* as the explicit target (the original honours
        ``sys.argv[1]`` exactly this way: "Path(sys.argv[1]) if
        len(sys.argv) > 1 else ROOT / 'mcp_servers.generated.json'").
        """
        original_argv = list(sys.argv)
        sys.argv = [sys.argv[0], str(output)]
        try:
            return main()
        finally:
            sys.argv = original_argv

    def generate_config(self, output: Path) -> int:
        return self.generate(output)

    # -- Block 3: Aggregate inspection verbs ---------------------------------------
    def list_servers(self) -> list[dict[str, object]]:
        """MCP-enabled tools from the manifest (original cmd_mcp 'list' logic)."""
        manifest_path = self._root / "config" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        servers = []
        for tool in manifest.get("tools", []):
            if not tool.get("isMcp", False):
                continue
            servers.append({
                "id": tool["id"],
                "category": tool.get("category", ""),
                "description": tool.get("description", ""),
            })
        return servers

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
def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else repo_root() / "mcp_servers.generated.json"
    print("Generating unified MCP client configuration...")
    print(f"Target: {output}")

    env = load_first_env([
        agents_arwaky_config_dir() / "anytype.env",
        config_home() / "anytype-mcp/.env",
        repo_root() / "config/anytype.env",
        repo_root() / ".env",
    ])
    anytype_base = env.get("ANYTYPE_API_BASE_URL", "http://127.0.0.1:31012")
    anytype_key = env.get("ANYTYPE_API_KEY", "<YOUR_API_KEY>")
    if not anytype_key or anytype_key in ("<YOUR_API_KEY>", "change-me", "<YOUR_ANYTYPE_API_KEY>", ""):
        print("  \u26a0 Warning: ANYTYPE_API_KEY is not set or is a placeholder.", file=sys.stderr)
        print("    Run 'aa anytype auth-key' to generate a valid key.", file=sys.stderr)
        anytype_key = "<YOUR_API_KEY>"

    # Single source of truth: manifest.json (Traceability fix — hapus hardcoded dict)
    manifest_path = repo_root() / "config" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config: dict = {"mcpServers": {}}
    for tool in manifest.get("tools", []):
        if not tool.get("isMcp", False):
            continue
        tool_id = tool["id"]
        # An MCP server often exposes a dedicated stdio binary that differs
        # from the CLI binary (e.g. vision-arwaky -> vision-arwaky-mcp).
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


