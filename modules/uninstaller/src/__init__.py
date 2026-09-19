"""Uninstaller feature: generic tool removal via two business-action
capabilities (remover, verifier) + single orchestrator agent.

Public API:
- UninstallerOrchestrator (agent): feature orchestrator
- IToolUninstaller / IToolRemover / IToolVerifier (contracts)
"""
from __future__ import annotations

from modules.uninstaller.src.agent_uninstaller_orchestrator import UninstallerOrchestrator
from modules.uninstaller.src.contract_tool_uninstaller_protocol import (
    IToolRemover,
    IToolUninstaller,
    IToolVerifier,
)

__all__ = ["IToolRemover", "IToolUninstaller", "IToolVerifier", "UninstallerOrchestrator"]
