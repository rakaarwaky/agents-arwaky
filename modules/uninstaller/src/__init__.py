"""Uninstaller feature: data-driven tool removal (AES7 orchestrator).

Public API:
- UninstallerOrchestrator (agent): feature orchestrator
- IToolUninstaller (contract): capability protocol
"""
from __future__ import annotations

from modules.uninstaller.src.agent_uninstaller_orchestrator import UninstallerOrchestrator
from modules.uninstaller.src.contract_tool_uninstaller import IToolUninstaller

__all__ = ["IToolUninstaller", "UninstallerOrchestrator"]
