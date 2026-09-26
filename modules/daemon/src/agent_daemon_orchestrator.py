"""Daemon agent orchestrator — single-execute aggregate over the daemon managers.

Dispatches each ``DaemonRequest.op`` to the matching rich protocol method on
the injected managers, then wraps the result in a ``DaemonOutcome``.
"""
from __future__ import annotations

from typing import ClassVar

from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_daemon_protocol import IDaemonProtocol
from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonOp,
    DaemonOutcome,
    DaemonRequest,
    DaemonResponse,
    DaemonUnit,
    ExitCode,
)

#: Daemon ids the orchestrator can route to, in listing order.
_KNOWN: tuple[DaemonName, ...] = (DaemonName("9router"), DaemonName("anytype"))


# ─── Block 1: Class Definition & Constructor ──────────────
class DaemonOrchestrator(IDaemonAggregate):
    """Route daemon actions to the named capability (zero I/O)."""

    def __init__(
        self,
        ninerouter: IDaemonProtocol,
        anytype: IDaemonProtocol | None = None,
    ) -> None:
        self._ninerouter = ninerouter
        self._anytype = anytype
        self._managers: dict[str, IDaemonProtocol] = {"9router": ninerouter}
        if anytype is not None:
            self._managers["anytype"] = anytype

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: DaemonRequest) -> DaemonResponse:
        """Route *request* to the matching protocol method; return the response."""
        op = DaemonOp(str(request.op))
        if op == "start":
            return _from_exit(self._require(_name(request)).start())
        if op == "stop":
            return _from_exit(self._require(_name(request)).stop())
        if op == "restart":
            return _from_exit(self._require(_name(request)).restart())
        if op == "status":
            return _from_status(self._require(_name(request)).status())
        if op == "logs":
            return _from_exit(self._require(_name(request)).logs())
        if op == "install_unit":
            return _from_exit(self._for_unit(_unit(request)).install_unit(_unit(request)))
        if op == "remove_unit":
            return _from_exit(self._for_unit(_unit(request)).remove_unit(_unit(request)))
        if op == "unit_status":
            return _from_exit(self._for_unit(_unit(request)).unit_status(_unit(request)))
        raise ValueError(f"Unknown daemon op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    #: systemd unit filename → daemon id (unit ops accept either form).
    _UNIT_DAEMON: ClassVar[dict[str, str]] = {
        "9router.service": "9router",
        "anytype-daemon.service": "anytype",
        "anytype.service": "anytype",
    }

    @property
    def known(self) -> tuple[DaemonName, ...]:
        """Names of the daemons this orchestrator can route to."""
        return _KNOWN

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


def _name(request: DaemonRequest) -> DaemonName:
    """Read the daemon name a request routes to; fall back to the first known id."""
    if request.name is None:
        return _KNOWN[0]
    return DaemonName(str(request.name))


def _unit(request: DaemonRequest) -> DaemonUnit:
    """Read the unit a request routes to; fall back to the first known unit."""
    if request.unit is None:
        return DaemonUnit("9router.service")
    return DaemonUnit(str(request.unit))


def _from_exit(code: ExitCode) -> DaemonOutcome:
    """Wrap an exit code in an outcome carrying no status snapshot."""
    return DaemonOutcome(success=code == 0, exit_code=int(code), message="")


def _from_status(status) -> DaemonOutcome:
    """Wrap a DaemonStatus snapshot in an outcome."""
    return DaemonOutcome(
        success=status.ok,
        exit_code=0 if status.ok else 1,
        status=status,
        message="",
    )


__all__ = [
    "DaemonName",
    "DaemonOp",
    "DaemonOrchestrator",
    "DaemonOutcome",
    "DaemonRequest",
    "DaemonResponse",
    "DaemonUnit",
    "ExitCode",
    "IDaemonAggregate",
    "IDaemonProtocol",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonName": DaemonName,
    "DaemonOp": DaemonOp,
    "DaemonOrchestrator": DaemonOrchestrator,
    "DaemonOutcome": DaemonOutcome,
    "DaemonRequest": DaemonRequest,
    "DaemonResponse": DaemonResponse,
    "DaemonUnit": DaemonUnit,
    "ExitCode": ExitCode,
}
