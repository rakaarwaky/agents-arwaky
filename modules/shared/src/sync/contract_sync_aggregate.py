"""Sync-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod


class ISyncAggregate(ABC):
    """Aggregate over the one-shot ecosystem sync."""

    @abstractmethod
    def sync(self, no_connect: bool, no_update: bool) -> int:
        """Run the full sync; return exit code."""
        raise NotImplementedError
