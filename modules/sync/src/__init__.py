"""Sync feature — public symbols.

Re-exports the orchestrator, container, and surface entry points so
feature consumers can import from ``modules.sync`` directly.
"""
from __future__ import annotations

from modules.sync.src.agent_sync_orchestrator import SyncOrchestrator
from modules.sync.src.capabilities_sync_runner import SyncRunner
from modules.sync.src.root_sync_container import SyncContainer, create_sync_feature
from modules.sync.src.surface_sync_command import cmd_sync

__all__ = [
    "SyncContainer",
    "SyncOrchestrator",
    "SyncRunner",
    "cmd_sync",
    "create_sync_feature",
]
