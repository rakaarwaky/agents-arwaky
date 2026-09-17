"""MCP surface — CLI adapter for aa mcp (list|generate|show)."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.logging.utility_logging import BOLD, RESET, err
from modules.shared.src.mcp.contract_mcp_aggregate import IMcpAggregate
from modules.shared.src.paths.utility_paths import repo_root


def cmd_mcp(args: list[str], orch: IMcpAggregate) -> int:
    """aa mcp [list|generate|show]"""
    action = args[0] if args else "list"
    if action == "list":
        print(f"{BOLD()}MCP-Enabled Tools:{RESET()}")
        for server in orch.list_servers():
            print(f"  - {server['id']} [{server['category']}]: {server['description']}")
        return 0
    if action == "generate":
        target = Path(args[1]) if len(args) > 1 else repo_root() / "mcp_servers.generated.json"
        return orch.generate_config(target)
    if action in {"show", "path"}:
        return orch.show_server()
    err(f"Unknown MCP action: {action}")
    print("Valid actions: list, generate, show")
    return 1
