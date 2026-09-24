"""Daemon feature — public symbols.

Re-exports the orchestrator, container, and surface entry points so
feature consumers can import from ``modules.daemon`` directly.
"""
from __future__ import annotations

from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
from modules.daemon.src.root_daemon_container import (
    DaemonContainer,
    create_daemon_feature,
)
from modules.daemon.src.surface_daemon_command import cmd_anytype, cmd_9router

__all__ = [
    "AnytypeDaemonManager",
    "DaemonContainer",
    "DaemonOrchestrator",
    "NinerouterDaemonManager",
    "cmd_anytype",
    "cmd_9router",
    "create_daemon_feature",
]
