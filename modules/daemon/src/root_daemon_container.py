"""Daemon composition root — wires daemon managers into the orchestrator."""
from __future__ import annotations

from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate


class DaemonContainer:
    """Construct both daemon managers and the routing orchestrator."""

    def __init__(self) -> None:
        ninerouter = NinerouterDaemonManager()
        anytype = AnytypeDaemonManager()
        self._orchestrator = DaemonOrchestrator(ninerouter, anytype)
        self._ninerouter = ninerouter
        self._anytype = anytype

    @property
    def aggregate(self) -> IDaemonAggregate:
        """The fully-wired DaemonOrchestrator."""
        return self._orchestrator

    @property
    def ninerouter(self) -> IDaemonAggregate:
        """The NinerouterDaemonManager facade."""
        return self._ninerouter

    @property
    def anytype(self) -> IDaemonAggregate:
        """The AnytypeDaemonManager facade."""
        return self._anytype


def create_daemon_feature() -> IDaemonAggregate:
    """Fully-wired daemon feature aggregate."""
    return DaemonContainer().aggregate
