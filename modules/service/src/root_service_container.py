"""Service composition root — wires the daemon aggregate into the service orchestrator.

Builds the daemon aggregate from the daemon feature's capability layer
(root layer is allowed to import capabilities) and injects it into the
service manager, avoiding a root->root import between composition layers.
"""
from __future__ import annotations

from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager
from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.taxonomy_daemon_vo import DaemonName, DaemonStatus, ExitCode
from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
from modules.service.src.capabilities_service_manager import ServiceManager
from modules.shared.src.contract_service_aggregate import IServiceAggregate


class DaemonAggregateAdapter(IDaemonAggregate):
    """IDaemonAggregate implementation over the two concrete daemon managers."""

    def __init__(self, omniroute: PodmanDaemonManager, anytype: AnytypeDaemonManager) -> None:
        self._managers = {"omniroute": omniroute, "anytype": anytype}

    def _mgr(self, name: DaemonName):
        return self._managers[name]

    def start_daemon(self, name: DaemonName) -> ExitCode:
        return self._mgr(name).start()

    def stop_daemon(self, name: DaemonName) -> ExitCode:
        return self._mgr(name).stop()

    def status_daemon(self, name: DaemonName) -> DaemonStatus:
        return self._mgr(name).status()

    def logs_daemon(self, name: DaemonName) -> ExitCode:
        return self._mgr(name).logs()

    def restart_daemon(self, name: DaemonName) -> ExitCode:
        return self._mgr(name).restart()


def create_service_feature() -> IServiceAggregate:
    """Fully-wired service feature aggregate."""
    return ServiceContainer().aggregate


class ServiceContainer:
    """Composition root: wires daemon managers into the service orchestrator."""

    def __init__(self) -> None:
        self._daemons = DaemonAggregateAdapter(PodmanDaemonManager(), AnytypeDaemonManager())
        self._manager = ServiceManager(daemons=self._daemons)
        self._orchestrator = ServiceOrchestrator(manager=self._manager)

    @property
    def aggregate(self) -> IServiceAggregate:
        return self._orchestrator

    @property
    def manager(self) -> ServiceManager:
        return self._manager

def cmd_service(args: list[str], orch: ServiceOrchestrator) -> int:
    """aa service <status|start|stop|restart|logs> [omniroute|anytype|all]."""
    if not args or args[0] in ("help", "-h", "--help"):
        return orch.help()
