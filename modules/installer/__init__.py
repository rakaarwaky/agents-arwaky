"""Installer feature — per-tool installer capabilities + orchestrator (AES).

Each tool has its own concrete capability file carrying the real install
logic (build commands, launcher names, entry points, ignore patterns,
tool-specific quirks) ported from the original tools/install/install_*.py
scripts. The orchestrator dispatches by tool id.
"""
from modules.installer.src.agent_installer_orchestrator import InstallerOrchestrator

__all__ = ["InstallerOrchestrator"]
