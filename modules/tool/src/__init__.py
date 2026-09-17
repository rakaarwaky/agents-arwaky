"""Tool feature — public symbols.

Re-exports the orchestrator, container, and surface entry points so
feature consumers can import from ``modules.tool`` directly.
"""
from __future__ import annotations

from modules.tool.src.agent_tool_orchestrator import ToolOrchestrator
from modules.tool.src.capabilities_tool_install import ToolInstaller
from modules.tool.src.capabilities_tool_resolver import ToolResolver
from modules.tool.src.capabilities_tool_uninstall import ToolUninstaller
from modules.tool.src.capabilities_tool_update import ToolUpdater
from modules.tool.src.root_tool_container import ToolContainer, create_tool_feature
from modules.tool.src.surface_tool_command import (
    cmd_install,
    cmd_list,
    cmd_run,
    cmd_tool,
    cmd_uninstall,
    cmd_update,
)

__all__ = [
    "ToolContainer",
    "ToolInstaller",
    "ToolOrchestrator",
    "ToolResolver",
    "ToolUninstaller",
    "ToolUpdater",
    "cmd_install",
    "cmd_list",
    "cmd_run",
    "cmd_tool",
    "cmd_uninstall",
    "cmd_update",
    "create_tool_feature",
]
