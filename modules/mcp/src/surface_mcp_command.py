"""MCP surface — CLI adapter for aa mcp (list|generate|show)."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.taxonomy_mcp_vo import McpAlias, McpServerId
from modules.shared.src.utility_logging_setup import BOLD, RESET, err
from modules.shared.src.utility_paths_resolver import repo_root


def cmd_mcp(args: list[str], orch: IMcpAggregate) -> int:
    """aa mcp [list|generate|show]"""
    if not args or args[0] in ("-h", "--help", "help"):
        print("Usage: aa mcp <list|generate|show> [path|server_id]")
        print()
        print("  list                Enumerate MCP-enabled tools")
        print("  generate [path]     Rebuild mcp_servers.generated.json")
        print("  show [server_id]    Inspect the config, or probe one server")
        print("  list --json         Machine-readable server list")
        return 0
    action = args[0]
    if action == "list":
        if "--json" in args:
            import json as _json
            servers = [
                {"id": s.id, "category": s.category, "description": s.description}
                for s in orch.list_servers()
            ]
            print(_json.dumps(servers, indent=2, ensure_ascii=False))
            return 0
        print(f"{BOLD()}MCP-Enabled Tools:{RESET()}")
        for server in orch.list_servers():
            print(f"  - {server.id} [{server.category}]: {server.description}")
        return 0
    if action == "generate":
        target = Path(args[1]) if len(args) > 1 and not args[1].startswith("-") else repo_root() / "mcp_servers.generated.json"
        return orch.generate(target)
    if action in {"show", "path"}:
        raw = args[1] if len(args) > 1 and not args[1].startswith("-") else None
        server_id = McpServerId(raw) if raw is not None else None
        return orch.show_server(server_id)
    if action == "alias":
        if len(args) < 3 or args[2].startswith("-"):
            err("Usage: aa mcp alias <name> <path>")
            return 1
        return orch.generate_alias(McpAlias(args[1]), Path(args[2]))
    if action == "validate":
        target = Path(args[1]) if len(args) > 1 and not args[1].startswith("-") else None
        return orch.validate(target)
    err(f"Unknown MCP action: {action}")
    print("Valid actions: list, generate, show, alias, validate")
    return 1


class McpAction(IMcpAggregate):
    """Agent-layer action surface for the mcp feature (AES405 aggregate implementor)."""

    def __init__(self, agg: IMcpAggregate) -> None:
        self._agg = agg

    def list_servers(self):
        """Return metadata for every registered MCP-enabled tool."""
        return self._agg.list_servers()

    def show_server(self, server_id: McpServerId | None = None):
        """Show the generated config or probe one server's help/schema."""
        return self._agg.show_server(server_id)

    def generate(self, output):
        """Build the unified MCP client config at *output*."""
        return self._agg.generate(output)

    def generate_alias(self, alias: McpAlias, output):
        """Write an alias-qualified client config via the same generator."""
        return self._agg.generate_alias(alias, output)

    def validate(self, output=None):
        """Parse the generated config at *output* and report validity."""
        return self._agg.validate(output)
