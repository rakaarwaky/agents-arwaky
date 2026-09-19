"""Updater feature: data-driven tool updates (AES7 orchestrator).

Public API:
- UpdaterOrchestrator (agent): single update verb (bumper → recorder)
- IToolUpdater / IToolBumper / IToolRecorder / IToolUpdaterAdapter (contract)
"""
from __future__ import annotations

from modules.updater.src.agent_updater_orchestrator import UpdaterOrchestrator
from modules.updater.src.contract_tool_updater_protocol import (
    IToolBumper,
    IToolRecorder,
    IToolUpdater,
    IToolUpdaterAdapter,
)

__all__ = [
    "IToolBumper",
    "IToolRecorder",
    "IToolUpdater",
    "IToolUpdaterAdapter",
    "UpdaterOrchestrator",
]
