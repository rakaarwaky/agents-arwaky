"""Service agent orchestrator — thin aggregate over the service manager."""
from __future__ import annotations

from modules.service.src.capabilities_service_manager import ServiceManager


class ServiceOrchestrator:
    """Delegates every service verb to the injected ServiceManager.

    # Block 1: Constructor
    # Block 2: Verb delegation
    # Block 3: Help
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, manager: ServiceManager) -> None:
        self._manager = manager

    # -- Block 2: Verb delegation ------------------------------------------------
    def status(self) -> int:
        return self._manager.status()

    def start(self, target: str = "all") -> int:
        return self._manager.start(target)

    def stop(self, target: str = "all") -> int:
        return self._manager.stop(target)

    def restart(self, target: str = "all") -> int:
        return self._manager.restart(target)

    def logs(self, target: str = "9router") -> int:
        return self._manager.logs(target)

    # -- Block 3: Help --------------------------------------------------------------
    def help(self) -> int:
        return self._manager.help()
