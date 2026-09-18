"""Shared tool-domain: taxonomy + contracts for tool capabilities.\n\nSelf-contained — no references back to ``common.*``.\n"""
from __future__ import annotations

from modules.shared.src.common.taxonomy_core_error import ArwakyError
from modules.shared.src.tool.contract_tool_aggregate import IToolAggregate
from modules.shared.src.tool.contract_tool_protocol import (
    IToolExecutor,
    IToolInstaller,
    IToolUninstaller,
    IToolUpdater,
)
from modules.shared.src.tool.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)

__all__ = [
    "ArwakyError",
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
