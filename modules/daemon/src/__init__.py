"""Daemon feature — public symbols.

Re-exports the orchestrator, container, and surface entry points so
feature consumers can import from ``modules.daemon`` directly.
"""
from __future__ import annotations

from modules.cli.src.surface_daemon_command import cmd_anytype, cmd_omniroute
from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.root_daemon_container import (
    DaemonContainer,
    create_daemon_feature,
)

__all__ = [
    "AnytypeDaemonManager",
    "DaemonContainer",
    "DaemonOrchestrator",
    "OmnirouteDaemonManager",
    "cmd_anytype",
    "cmd_omniroute",
    "create_daemon_feature",
]
