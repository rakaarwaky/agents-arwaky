"""Daemon composition root — wires daemon managers into the orchestrator."""
from __future__ import annotations

from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager
from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate


class DaemonContainer:
    """Construct the daemon managers and the routing orchestrator."""

    def __init__(self) -> None:
        anytype = AnytypeDaemonManager()
        omniroute = OmnirouteDaemonManager()
        self._orchestrator = DaemonOrchestrator(anytype, omniroute)
        self._anytype = anytype
        self._omniroute = omniroute

    @property
    def aggregate(self) -> IDaemonAggregate:
        """The fully-wired DaemonOrchestrator."""
        return self._orchestrator

    @property
    def anytype(self):
        """The AnytypeDaemonManager instance."""
        return self._anytype

    @property
    def omniroute(self):
        """The OmnirouteDaemonManager instance."""
        return self._omniroute


def create_daemon_feature() -> IDaemonAggregate:
    """Fully-wired daemon feature aggregate."""
    return DaemonContainer().aggregate
