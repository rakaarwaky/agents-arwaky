"""Service composition root — wires daemon managers into the service orchestrator."""
from __future__ import annotations

from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_ninerouter_daemon import PodmanDaemonManager
from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
from modules.service.src.capabilities_service_manager import ServiceManager


class ServiceContainer:
    """Construct the daemon managers, the service manager, and the orchestrator."""

    def __init__(self) -> None:
        manager = ServiceManager(PodmanDaemonManager(), AnytypeDaemonManager())
        self._orchestrator = ServiceOrchestrator(manager)

    @property
    def aggregate(self) -> ServiceOrchestrator:
        return self._orchestrator


def create_service_feature() -> ServiceOrchestrator:
    """Fully-wired service feature aggregate."""
    return ServiceContainer().aggregate
