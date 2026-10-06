"""MCP surface — CLI adapter for aa mcp (list|generate|show|alias|validate)."""
from __future__ import annotations

import json as _json
from pathlib import Path

from modules.shared.src.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.taxonomy_mcp_vo import (
    McpAlias,
    McpOp,
    McpRequest,
    McpServerId,
)
from modules.shared.src.utility_logging_setup import BOLD, RESET, err
from modules.shared.src.utility_paths_resolver import repo_root


def cmd_mcp(args: list[str], orch: IMcpAggregate) -> int:
    """aa mcp [list|generate|show|alias|validate] [path|server_id]"""
    if not args or args[0] in ("-h", "--help", "help"):
        print("Usage: aa mcp <list|generate|show|alias|validate> [path|server_id]")
        print()
        print("  list                Enumerate MCP-enabled tools")
        print("  generate [path]     Rebuild mcp_servers.generated.json")
        print("  show [server_id]    Inspect the config, or probe one server")
        print("  list --json         Machine-readable server list")
        return 0
    action = args[0]
    if action == "list":
        if "--json" in args:
            response = orch.execute(McpRequest(McpOp("list")))
            servers = [
                {"id": s.id, "category": s.category, "description": s.description}
                for s in response
            ]
            print(_json.dumps(servers, indent=2, ensure_ascii=False))
            return 0
        response = orch.execute(McpRequest(McpOp("list")))
        print(f"{BOLD()}MCP-Enabled Tools:{RESET()}")
        for server in response:
            print(f"  - {server.id} [{server.category}]: {server.description}")
        return 0
    if action == "generate":
        target = Path(args[1]) if len(args) > 1 and not args[1].startswith("-") else repo_root() / "mcp_servers.generated.json"
        return int(orch.execute(McpRequest(McpOp("generate"), output=target)))
    if action in {"show", "path"}:
        raw = args[1] if len(args) > 1 and not args[1].startswith("-") else None
        server_id = McpServerId(raw) if raw is not None else None
        return int(orch.execute(McpRequest(McpOp("show"), server_id=server_id)))
    if action == "alias":
        if len(args) < 3 or args[2].startswith("-"):
            err("Usage: aa mcp alias <name> <path>")
            return 1
        target = Path(args[2])
        return int(orch.execute(McpRequest(McpOp("alias"), alias=McpAlias(args[1]), output=target)))
    if action == "validate":
        target = Path(args[1]) if len(args) > 1 and not args[1].startswith("-") else None
        return int(orch.execute(McpRequest(McpOp("validate"), output=target)))
    err(f"Unknown MCP action: {action}")
    print("Valid actions: list, generate, show, alias, validate")
    return 1


class McpAction(IMcpAggregate):
    """Aggregate implementor wrapping another aggregate (surface-layer facade)."""

    def __init__(self, agg: IMcpAggregate) -> None:
        self._agg = agg

    def execute(self, request: McpRequest) -> object:
        """Delegate the request to the wrapped aggregate unchanged."""
        return self._agg.execute(request)


__all__ = ["McpAction", "cmd_mcp"]
