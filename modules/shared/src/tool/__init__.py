"""Shared tool-domain: taxonomy + executor contract.

Feature-specific protocol contracts live in their respective feature modules:
- installer: modules.installer.src.contract_tool_installer
- updater: modules.updater.src.contract_tool_updater
- uninstaller: modules.uninstaller.src.contract_tool_uninstaller
- runner: modules.runner.src.contract_tool_runner (aggregate)
"""
from __future__ import annotations

from modules.shared.src.tool.contract_tool_protocol import IToolExecutor
from modules.shared.src.tool.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)

__all__ = [
    "InstallResult",
    "IToolExecutor",
    "ToolSpec",
    "UninstallResult",
    "UpdateResult",
]
