"""Sync agent orchestrator — thin aggregate over the sync runner."""
from __future__ import annotations

from modules.sync.contract.contract_sync_aggregate import ISyncAggregate
from modules.sync.src.capabilities_sync_runner import SyncRunner


class SyncOrchestrator(ISyncAggregate):
    """Delegate the one-shot sync to the injected runner.

    # Block 1: Constructor
    # Block 2: sync delegation
    # Block 3: (reserved for pre/post hooks)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, runner: SyncRunner) -> None:
        self._runner = runner

    # -- Block 2: sync delegation ----------------------------------------------------
    def sync(self, no_connect: bool, no_update: bool) -> int:
        return self._runner.run(no_connect, no_update)
