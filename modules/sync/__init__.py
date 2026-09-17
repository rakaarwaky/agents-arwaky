"""Sync feature package — update + mcp generate + connect + check pipeline.

Public re-exports: orchestrator + container.
"""
from __future__ import annotations

from modules.sync.src import (
    SyncContainer,
    SyncOrchestrator,
    create_sync_feature,
)

__all__ = [
    "SyncContainer",
    "SyncOrchestrator",
    "create_sync_feature",
]
