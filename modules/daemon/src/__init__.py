"""Daemon feature — public symbols.

Re-exports the orchestrator, container, and surface entry points so
feature consumers can import from ``modules.daemon`` directly.
"""
from __future__ import annotations

from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_ninerouter_daemon import PodmanDaemonManager
from modules.daemon.src.root_daemon_container import DaemonContainer, create_daemon_feature
from modules.cli.src.surface_daemon_command import cmd_9router, cmd_anytype

__all__ = [
    "AnytypeDaemonManager",
    "DaemonContainer",
    "DaemonOrchestrator",
    "PodmanDaemonManager",
    "cmd_9router",
    "cmd_anytype",
    "create_daemon_feature",
]
