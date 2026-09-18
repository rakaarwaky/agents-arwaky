"""Shared tool-domain: taxonomy + contracts for tool capabilities."""
from modules.shared.src.common.tool.contract_tool_aggregate import IToolAggregate
from modules.shared.src.common.tool.contract_tool_protocol import (
    IToolExecutor,
    IToolInstaller,
    IToolUninstaller,
    IToolUpdater,
)
from modules.shared.src.common.tool.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)

__all__ = [
    "IToolAggregate",
    "IToolExecutor",
    "IToolInstaller",
    "IToolUninstaller",
    "IToolUpdater",
    "InstallResult",
    "ToolSpec",
    "UninstallResult",
    "UpdateResult",
]
