"""Daemon composition root — wires daemon managers into the orchestrator."""
from __future__ import annotations

from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
from modules.daemon.src.capabilities_9router_import_omniroute import (
    NineRouterImportOmniroute,
)
from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager
from modules.shared.src.daemon.contract_daemon_aggregate import IDaemonAggregate


class DaemonContainer:
    """Construct the daemon managers and the routing orchestrator."""

    def __init__(self) -> None:
        omniroute = OmnirouteDaemonManager()
        nine_import = NineRouterImportOmniroute()
        ninerouter = NinerouterDaemonManager(import_omni=nine_import)
        self._orchestrator = DaemonOrchestrator(omniroute, ninerouter)
        self._omniroute = omniroute
        self._ninerouter = ninerouter

    @property
    def aggregate(self) -> IDaemonAggregate:
        """The fully-wired DaemonOrchestrator."""
        return self._orchestrator

    @property
    def ninerouter(self):
        """The NinerouterDaemonManager instance."""
        return self._ninerouter

    @property
    def omniroute(self):
        """The OmnirouteDaemonManager instance."""
        return self._omniroute


def create_daemon_feature() -> IDaemonAggregate:
    """Fully-wired daemon feature aggregate."""
    return DaemonContainer().aggregate
