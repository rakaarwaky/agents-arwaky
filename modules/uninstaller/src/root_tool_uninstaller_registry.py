"""Root composition — uninstaller wiring (AES7).

The AES root layer is the only layer allowed to import `capabilities*`;
this module centralises the remover+verifier composition so that
`agent_uninstaller_orchestrator` stays capability-free (AES201 rule 8).
"""
from __future__ import annotations

from modules.daemon.src.root_daemon_container import create_daemon_feature
from modules.uninstaller.src.agent_uninstaller_orchestrator import (
    UninstallerOrchestrator,
)

__all__ = ["build_uninstaller_orchestrator"]


def build_uninstaller_orchestrator() -> UninstallerOrchestrator:
    """Instantiate the uninstaller agent with the daemon aggregate injected."""
    return UninstallerOrchestrator(daemons=create_daemon_feature())
