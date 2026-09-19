"""Tools feature — unified install / update / uninstall / run (AES).

Merged from the four former features (installer, updater, uninstaller,
runner): one `ToolsOrchestrator` agent, eight business-action
capabilities, thirteen unified per-tool adapters (one per manifest tool
id), and the zero-I/O `create_tools_feature()` composition root.
"""
from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
from modules.tools.src.root_tools_container import create_tools_feature

#: Backwards-compatible alias for the old runner aggregate.
ToolOrchestrator = ToolsOrchestrator

__all__ = [
    "ToolOrchestrator",
    "ToolsOrchestrator",
    "create_tools_feature",
]
