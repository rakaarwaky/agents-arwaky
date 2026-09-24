"""Daemon agent orchestrator — routes actions by daemon name or unit."""
from __future__ import annotations

from typing import ClassVar

from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_daemon_protocol import IDaemonProtocol
from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonStatus,
    DaemonUnit,
    ExitCode,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class DaemonOrchestrator(IDaemonAggregate):
    """Route daemon actions to the named capability (zero I/O)."""

    def __init__(
        self,
        ninerouter: IDaemonProtocol,
        anytype: IDaemonProtocol,
    ) -> None:
        self._ninerouter = ninerouter
        self._anytype = anytype
        self._managers: dict[str, IDaemonProtocol] = {
            "9router": ninerouter,
            "anytype": anytype,
        }

    # ─── Block 2: Aggregate Method Implementation ──────────
    def list_known(self) -> tuple[DaemonName, ...]:
        return (DaemonName("9router"), DaemonName("anytype"))

    def start(self, name: DaemonName) -> ExitCode:
        return ExitCode(int(self._require(name).execute("start")))

    def stop(self, name: DaemonName) -> ExitCode:
        return ExitCode(int(self._require(name).execute("stop")))

    def restart(self, name: DaemonName) -> ExitCode:
        return ExitCode(int(self._require(name).execute("restart")))

    def status(self, name: DaemonName) -> DaemonStatus:
        result = self._require(name).execute("status")
        if not isinstance(result, DaemonStatus):
            raise TypeError(f"status op for {name!r} did not return a DaemonStatus")
        return result

    def logs(self, name: DaemonName) -> ExitCode:
        return ExitCode(int(self._require(name).execute("logs")))

    def install_unit(self, unit: DaemonUnit) -> ExitCode:
        return ExitCode(int(self._for_unit(unit).execute("install_unit", unit=unit)))

    def remove_unit(self, unit: DaemonUnit) -> ExitCode:
        return ExitCode(int(self._for_unit(unit).execute("remove_unit", unit=unit)))

    def unit_status(self, unit: DaemonUnit) -> ExitCode:
        return ExitCode(int(self._for_unit(unit).execute("unit_status", unit=unit)))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    #: systemd unit filename → daemon id (unit ops accept either form).
    _UNIT_DAEMON: ClassVar[dict[str, str]] = {
        "9router.service": "9router",
        "anytype-daemon.service": "anytype",
        "anytype.service": "anytype",
    }

    def _manager(self, name: DaemonName) -> IDaemonProtocol | None:
        return self._managers.get(str(name).lower())

    def _require(self, name: DaemonName) -> IDaemonProtocol:
        manager = self._manager(name)
        if manager is None:
            raise ValueError(f"Unknown daemon: {name}")
        return manager

    def _for_unit(self, unit: str) -> IDaemonProtocol:
        key = unit if unit.endswith(".service") else f"{unit}.service"
        daemon = self._UNIT_DAEMON.get(key) or self._UNIT_DAEMON.get(unit)
        if daemon is None and unit in self._managers:
            daemon = unit
        if daemon is None:
            raise ValueError(f"Unknown unit: {unit}")
        return self._require(DaemonName(daemon))

    def __repr__(self) -> str:
        return "DaemonOrchestrator()"


__all__ = [
    "DaemonName",
    "DaemonOrchestrator",
    "DaemonStatus",
    "ExitCode",
    "IDaemonAggregate",
    "IDaemonProtocol",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonName": DaemonName,
    "DaemonOrchestrator": DaemonOrchestrator,
    "DaemonStatus": DaemonStatus,
    "ExitCode": ExitCode,
}
