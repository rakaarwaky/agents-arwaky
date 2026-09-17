"""Uninstaller feature — per-tool uninstall capabilities + orchestrator (AES).

Each tool has its own concrete capability file carrying the real uninstall
logic (per-tool launcher lists, tool keys, daemon/secrets cleanup) ported
from the original tools/uninstall/uninstall_*.py scripts. The orchestrator
dispatches by tool id.
"""
from modules.uninstaller.src.agent_uninstaller_orchestrator import UninstallerOrchestrator

__all__ = ["UninstallerOrchestrator"]
