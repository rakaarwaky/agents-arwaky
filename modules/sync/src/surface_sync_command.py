"""Sync surface — CLI adapter for aa sync."""
from __future__ import annotations

from modules.sync.contract.contract_sync_aggregate import ISyncAggregate


def cmd_sync(args: list[str], orch: ISyncAggregate) -> int:
    """aa sync [--no-connect] [--no-update]."""
    if args and args[0] in ("-h", "--help", "help"):
        print("Usage: aa sync [--no-connect] [--no-update]")
        print()
        print("One-shot ecosystem sync (4 steps):")
        print("  1. update tools (pull + reinstall)   --no-update skips step 1")
        print("  2. generate MCP config")
        print("  3. reconnect harnesses               --no-connect skips step 3")
        print("  4. verify (aa check)")
        return 0
    no_connect = "--no-connect" in args
    no_update = "--no-update" in args
    return orch.sync(no_connect, no_update)
