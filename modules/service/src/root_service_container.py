"""Service composition root — wires the daemon aggregate into the service orchestrator.

Builds the daemon aggregate from the daemon feature's capability layer
(root layer is allowed to import capabilities) and injects it into the
service manager, avoiding a root->root import between composition layers.
"""
from __future__ import annotations

from typing import ClassVar

from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
from modules.service.src.capabilities_service_manager import ServiceManager
from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_service_aggregate import IServiceAggregate
from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonOp,
    DaemonOutcome,
    DaemonRequest,
    DaemonResponse,
    DaemonUnit,
)


class DaemonAggregateAdapter(IDaemonAggregate):
    """Single-execute IDaemonAggregate over the two concrete daemon managers."""

    _UNIT_DAEMON: ClassVar[dict[str, str]] = {
        "9router.service": "9router",
        "anytype-daemon.service": "anytype",
        "anytype.service": "anytype",
    }

    def __init__(self, ninerouter: NinerouterDaemonManager, anytype: AnytypeDaemonManager) -> None:
        self._managers = {"9router": ninerouter, "anytype": anytype}

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

    def execute(self, request: DaemonRequest) -> DaemonResponse:
        """Route *request* to the matching manager method; return the outcome."""
        op = DaemonOp(str(request.op))
        name = DaemonName(str(request.name)) if request.name else DaemonName("9router")
        unit = DaemonUnit(str(request.unit)) if request.unit else DaemonUnit("9router.service")
        if op == "start":
            return _exit(self._mgr(name).start())
        if op == "stop":
            return _exit(self._mgr(name).stop())
        if op == "restart":
            return _exit(self._mgr(name).restart())
        if op == "status":
            return _status(self._mgr(name).status())
        if op == "logs":
            return _exit(self._mgr(name).logs())
        if op == "install_unit":
            return _exit(self._for_unit(str(unit)).install_unit(unit))
        if op == "remove_unit":
            return _exit(self._for_unit(str(unit)).remove_unit(unit))
        if op == "unit_status":
            return _exit(self._for_unit(str(unit)).unit_status(unit))
        raise ValueError(f"Unknown daemon op: {op}")


def _exit(code) -> DaemonOutcome:
    """Wrap an exit code in a DaemonOutcome carrying no status snapshot."""
    return DaemonOutcome(success=code == 0, exit_code=int(code), message="")


def _status(snap) -> DaemonOutcome:
    """Wrap a DaemonStatus snapshot in a DaemonOutcome."""
    return DaemonOutcome(success=snap.ok, exit_code=0 if snap.ok else 1, status=snap, message="")


class ServiceContainer:
    """Composition root: wires daemon managers into the service orchestrator."""

    def __init__(self) -> None:
        self._daemons = DaemonAggregateAdapter(NinerouterDaemonManager(), AnytypeDaemonManager())
        self._manager = ServiceManager(daemons=self._daemons)
        self._orchestrator = ServiceOrchestrator(manager=self._manager)

    @property
    def aggregate(self) -> IServiceAggregate:
        """Expose the service orchestrator as the feature's public aggregate."""
        return self._orchestrator

    @property
    def manager(self) -> ServiceManager:
        """Expose the service manager for direct delegation."""
        return self._manager


def create_service_feature() -> IServiceAggregate:
    """Fully-wired service feature aggregate."""
    return ServiceContainer().aggregate