"""Uninstaller feature — generic tool removal (AES).

Removal is a business action organised into two capabilities:
- remover: stop daemon (if applicable), remove launchers + XDG state
- verifier: confirm the owned set is gone, surface named residuals

Per-tool differences are DATA (manifest + XDG layout), not code.
"""
from modules.uninstaller.src.agent_uninstaller_orchestrator import UninstallerOrchestrator

__all__ = ["UninstallerOrchestrator"]
