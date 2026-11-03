"""Daemon feature package — OmniRoute + 9router daemon lifecycle.

Public re-exports: orchestrator + container.
"""
from __future__ import annotations

from modules.cli.src.surface_daemon_command import (
    cmd_9router,
    cmd_omniroute,
)
from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager
from modules.daemon.src.root_daemon_container import (
    DaemonContainer,
    create_daemon_feature,
)

__all__ = [
    "DaemonContainer",
    "DaemonOrchestrator",
    "NinerouterDaemonManager",
    "OmnirouteDaemonManager",
    "cmd_9router",
    "cmd_omniroute",
    "create_daemon_feature",
]
