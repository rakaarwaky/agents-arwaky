"""Daemon composition root — wires daemon managers into the orchestrator."""
from __future__ import annotations

from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_ninerouter_daemon import PodmanDaemonManager
from modules.daemon.contract.contract_daemon_aggregate import IDaemonAggregate


class DaemonContainer:
    """Construct both daemon managers and the routing orchestrator."""

    def __init__(self) -> None:
        ninerouter = PodmanDaemonManager()
        anytype = AnytypeDaemonManager()
        self._orchestrator = DaemonOrchestrator(ninerouter, anytype)
        self._ninerouter = ninerouter
        self._anytype = anytype

    @property
    def aggregate(self) -> IDaemonAggregate:
        return self._orchestrator

    @property
    def ninerouter(self) -> PodmanDaemonManager:
        return self._ninerouter

    @property
    def anytype(self) -> AnytypeDaemonManager:
        return self._anytype


def create_daemon_feature() -> IDaemonAggregate:
    """Fully-wired daemon feature aggregate."""
    return DaemonContainer().aggregate
