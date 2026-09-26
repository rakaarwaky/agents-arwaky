"""Tools feature — unified install / update / uninstall / run (AES).

The four former features (installer, updater, uninstaller, runner) are
merged here: four action capability classes (install/update/uninstall/run,
each multi-method), one agent orchestrator,
thirteen unified per-tool adapters (one per manifest tool id), and the
zero-I/O `ToolsOrchestrator` aggregate.
"""
from modules.tools.src.root_tools_container import create_tools_feature

__all__ = ["create_tools_feature"]
