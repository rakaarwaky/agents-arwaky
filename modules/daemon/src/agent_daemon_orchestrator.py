"""Daemon agent orchestrator — routes verbs by daemon name."""
from __future__ import annotations

from modules.daemon.src.contract_daemon_aggregate import IDaemonAggregate
from modules.daemon.src.contract_daemon_protocol import IDaemonManager
from modules.daemon.src.taxonomy_daemon_vo import DaemonStatus


class DaemonOrchestrator(IDaemonAggregate):
    """Route daemon verbs to the named manager (zero I/O).

    # Block 1: Constructor (manager registry)
    # Block 2: Verb routing helpers
    # Block 3: Aggregate verb delegation
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        ninerouter: IDaemonManager,
        anytype: IDaemonManager,
    ) -> None:
        self._ninerouter = ninerouter
        self._anytype = anytype
        self._managers: dict[str, IDaemonManager] = {
            "9router": ninerouter,
            "ninerouter": ninerouter,
            "anytype": anytype,
        }

    # -- Block 2: Verb routing ---------------------------------------------------
    def _manager(self, name: str) -> IDaemonManager | None:
        return self._managers.get(name.lower())

    def known_daemons(self) -> tuple[str, ...]:
        return ("9router", "anytype")

    # -- Block 3: Aggregate verb delegation --------------------------------------
    def start_daemon(self, name: str) -> int:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager.start()

    def stop_daemon(self, name: str) -> int:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager.stop()

    def status_daemon(self, name: str) -> DaemonStatus:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager.status()

    def logs_daemon(self, name: str) -> int:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager.logs()

    def restart_daemon(self, name: str) -> int:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager.restart()

    def service_install(self, name: str) -> int:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager.service_install()

    def service_uninstall(self, name: str) -> int:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager.service_uninstall()

    def service_status(self, name: str) -> int:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager.service_status()
