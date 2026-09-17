"""Updater feature — per-tool updater capabilities + orchestrator (AES).

Each tool has its own concrete capability file carrying the real update
logic (submodule pull, force rebuild/reinstall, launcher rewrite) ported
from the original tools/update/update_*.py scripts. The orchestrator
dispatches by tool id.
"""
from modules.updater.src.agent_updater_orchestrator import UpdaterOrchestrator

__all__ = ["UpdaterOrchestrator"]
