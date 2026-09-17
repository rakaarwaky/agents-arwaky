"""Sync surface — CLI adapter for aa sync."""
from __future__ import annotations

from modules.shared.src.sync.contract_sync_aggregate import ISyncAggregate


def cmd_sync(args: list[str], orch: ISyncAggregate) -> int:
    """aa sync [--no-connect] [--no-update]."""
    no_connect = "--no-connect" in args
    no_update = "--no-update" in args
    return orch.sync(no_connect, no_update)
