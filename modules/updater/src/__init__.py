"""Updater feature: data-driven tool updates (AES7 orchestrator).

Public API:
- UpdaterOrchestrator (agent): feature orchestrator
- IToolUpdater (contract): capability protocol
"""
from __future__ import annotations

from modules.updater.src.agent_updater_orchestrator import UpdaterOrchestrator
from modules.updater.src.contract_tool_updater_protocol import IToolUpdater

__all__ = ["IToolUpdater", "UpdaterOrchestrator"]
