"""Sync composition root — wires the sync runner into the orchestrator."""
from __future__ import annotations

from modules.shared.src.sync.contract_sync_aggregate import ISyncAggregate
from modules.sync.src.agent_sync_orchestrator import SyncOrchestrator
from modules.sync.src.capabilities_sync_runner import SyncRunner


class SyncContainer:
    """Construct the sync runner and the orchestrator."""

    def __init__(self) -> None:
        runner = SyncRunner()
        self._orchestrator = SyncOrchestrator(runner)

    @property
    def aggregate(self) -> ISyncAggregate:
        return self._orchestrator


def create_sync_feature() -> ISyncAggregate:
    """Fully-wired sync feature aggregate."""
    return SyncContainer().aggregate
