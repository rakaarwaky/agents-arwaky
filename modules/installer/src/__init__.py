"""Installer feature: data-driven tool installation (AES7 orchestrator).

Public API:
- InstallerOrchestrator (agent): feature orchestrator
- IToolInstaller / IToolProvisioner / IToolLauncherRegistrar / IToolAdapter (contracts)
"""
from __future__ import annotations

from modules.installer.src.agent_installer_orchestrator import InstallerOrchestrator
from modules.installer.src.contract_tool_installer_protocol import (
    IToolAdapter,
    IToolInstaller,
    IToolLauncherRegistrar,
    IToolProvisioner,
)

__all__ = [
    "IToolAdapter",
    "IToolInstaller",
    "IToolLauncherRegistrar",
    "IToolProvisioner",
    "InstallerOrchestrator",
]
