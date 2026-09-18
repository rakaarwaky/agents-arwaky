"""Shared sync-domain: contracts for the one-shot ecosystem sync."""
from modules.shared.src.sync.contract_sync_aggregate import ISyncAggregate
from modules.shared.src.sync.contract_sync_protocol import ISyncRunner

__all__ = ["ISyncAggregate", "ISyncRunner"]
