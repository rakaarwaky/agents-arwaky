"""Service composition root — wires the daemon aggregate into the service orchestrator.

Builds the daemon aggregate from the daemon feature's capability layer
(root layer is allowed to import capabilities) and injects it into the
service manager, avoiding a root->root import between composition layers.
"""
from __future__ import annotations

from typing import ClassVar

from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager
from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
from modules.service.src.capabilities_service_manager import ServiceManager
from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_service_aggregate import IServiceAggregate
from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonStatus,
    DaemonUnit,
    ExitCode,
)


class DaemonAggregateAdapter(IDaemonAggregate):
    """IDaemonAggregate implementation over the two concrete daemon managers."""

    _UNIT_DAEMON: ClassVar[dict[str, str]] = {
        "omniroute.service": "omniroute",
        "anytype-daemon.service": "anytype",
        "anytype.service": "anytype",
    }

    def __init__(self, omniroute: PodmanDaemonManager, anytype: AnytypeDaemonManager) -> None:
        self._managers = {"omniroute": omniroute, "anytype": anytype}

    def _mgr(self, name: DaemonName):
        return self._managers[str(name).lower()]

    def _for_unit(self, unit: str):
        key = unit if unit.endswith(".service") else f"{unit}.service"
        daemon = self._UNIT_DAEMON.get(key) or self._UNIT_DAEMON.get(unit)
        if daemon is None and unit in self._managers:
            daemon = unit
        if daemon is None:
            raise ValueError(f"Unknown unit: {unit}")
        return self._managers[daemon]

    def list_known(self) -> tuple[DaemonName, ...]:
        return (DaemonName("omniroute"), DaemonName("anytype"))

    def start(self, name: DaemonName) -> ExitCode:
        return ExitCode(int(self._mgr(name).execute("start")))

    def stop(self, name: DaemonName) -> ExitCode:
        return ExitCode(int(self._mgr(name).execute("stop")))

    def restart(self, name: DaemonName) -> ExitCode:
        return ExitCode(int(self._mgr(name).execute("restart")))

    def status(self, name: DaemonName) -> DaemonStatus:
        result = self._mgr(name).execute("status")
        if not isinstance(result, DaemonStatus):
            raise TypeError(f"status op for {name!r} did not return a DaemonStatus")
        return result

    def logs(self, name: DaemonName) -> ExitCode:
        return ExitCode(int(self._mgr(name).execute("logs")))

    def install_unit(self, unit: DaemonUnit) -> ExitCode:
        return ExitCode(int(self._for_unit(unit).execute("install_unit", unit=unit)))

    def remove_unit(self, unit: DaemonUnit) -> ExitCode:
        return ExitCode(int(self._for_unit(unit).execute("remove_unit", unit=unit)))

    def unit_status(self, unit: DaemonUnit) -> ExitCode:
        return ExitCode(int(self._for_unit(unit).execute("unit_status", unit=unit)))


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
