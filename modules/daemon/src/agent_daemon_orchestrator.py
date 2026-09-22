"""Daemon agent orchestrator — routes verbs by daemon name."""
from __future__ import annotations

from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_daemon_protocol import IDaemonManager
from modules.shared.src.taxonomy_daemon_vo import DaemonName, DaemonStatus, ExitCode


class DaemonOrchestrator(IDaemonAggregate):
    """Route daemon verbs to the named manager (zero I/O).

    # Block 1: Constructor (manager registry)
    # Block 2: Verb routing helpers
    # Block 3: Aggregate verb delegation
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        omniroute: IDaemonManager,
        anytype: IDaemonManager,
    ) -> None:
        self._omniroute = omniroute
        self._anytype = anytype
        self._managers: dict[str, IDaemonManager] = {
            "omniroute": omniroute,
            "anytype": anytype,
        }

    # -- Block 2: Verb routing ---------------------------------------------------
    def _manager(self, name: DaemonName) -> IDaemonManager | None:
        return self._managers.get(name.lower())

    def known_daemons(self) -> tuple[str, ...]:
        return ("omniroute", "anytype")

    # -- Block 3: Aggregate verb delegation --------------------------------------
    def start_daemon(self, name: DaemonName) -> ExitCode:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return ExitCode(manager.start())

    def stop_daemon(self, name: DaemonName) -> ExitCode:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return ExitCode(manager.stop())

    def status_daemon(self, name: DaemonName) -> DaemonStatus:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager.status()

    def logs_daemon(self, name: DaemonName) -> ExitCode:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return ExitCode(manager.logs())

    def restart_daemon(self, name: DaemonName) -> ExitCode:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return ExitCode(manager.restart())

    def service_install(self, name: DaemonName) -> ExitCode:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return ExitCode(manager.service_install())

    def service_uninstall(self, name: DaemonName) -> ExitCode:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return ExitCode(manager.service_uninstall())

    def service_status(self, name: DaemonName) -> ExitCode:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return ExitCode(manager.service_status())

__all__ = ['DaemonName', 'DaemonOrchestrator', 'DaemonStatus', 'ExitCode', 'IDaemonAggregate', 'IDaemonManager']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonName": DaemonName,
    "DaemonOrchestrator": DaemonOrchestrator,
    "DaemonStatus": DaemonStatus,
    "ExitCode": ExitCode,
}
