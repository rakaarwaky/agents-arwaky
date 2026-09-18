"""Installer feature: data-driven tool installation (AES7 orchestrator).

Public API:
- InstallerOrchestrator (agent): feature orchestrator
- IToolInstaller (contract): capability protocol
"""
from __future__ import annotations

from modules.installer.src.agent_installer_orchestrator import InstallerOrchestrator
from modules.installer.src.contract_tool_installer import IToolInstaller

__all__ = ["IToolInstaller", "InstallerOrchestrator"]
