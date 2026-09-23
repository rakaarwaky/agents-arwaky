"""Daemon-domain protocol contracts (capability ABCs).

One feature → one protocol ABC (HOW-TO rule 3). ``IDaemonProtocol`` is the
single-method capability surface every daemon manager implements;
``IDaemonControlProtocol`` is a composite DI type of the five leaf control
protocols (no methods of its own) so the service capability can depend on a
narrow multi-daemon control surface without importing the aggregate.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonOp,
    DaemonStatus,
    DaemonUnit,
    ExitCode,
)


class IDaemonProtocol(ABC):
    """Capability contract for one daemon manager (one ``execute`` entry)."""

    @abstractmethod
    def execute(
        self,
        op: DaemonOp,
        name: DaemonName | None = None,
        unit: DaemonUnit | None = None,
    ) -> ExitCode | DaemonStatus:
        """Run one daemon operation under *op*; return exit code or status snapshot.

        Args:
            op: Operation token — lifecycle (`start`, `stop`, `restart`,
                `status`, `logs`), unit ops (`install_unit`, `remove_unit`,
                `unit_status`), or a capability-specific action.
            name: Optional daemon/account name or argument for the op.
            unit: Optional systemd unit the op applies to.
        """
        ...


class IDaemonStartProtocol(ABC):
    """FR: start the named daemon."""

    @abstractmethod
    def start(self, name: DaemonName) -> ExitCode:
        """Start *name*; return exit code."""
        ...


class IDaemonStopProtocol(ABC):
    """FR: stop the named daemon."""

    @abstractmethod
    def stop(self, name: DaemonName) -> ExitCode:
        """Stop *name*; return exit code."""
        ...


class IDaemonRestartProtocol(ABC):
    """FR: restart the named daemon."""

    @abstractmethod
    def restart(self, name: DaemonName) -> ExitCode:
        """Restart *name*; return exit code."""
        ...


class IDaemonStatusProtocol(ABC):
    """FR: report health of the named daemon."""

    @abstractmethod
    def status(self, name: DaemonName) -> DaemonStatus:
        """Health snapshot for *name*."""
        ...


class IDaemonLogsProtocol(ABC):
    """FR: tail logs of the named daemon."""

    @abstractmethod
    def logs(self, name: DaemonName) -> ExitCode:
        """Tail *name*'s logs; return exit code."""
        ...


class IDaemonControlProtocol(
    IDaemonStartProtocol,
    IDaemonStopProtocol,
    IDaemonRestartProtocol,
    IDaemonStatusProtocol,
    IDaemonLogsProtocol,
):
    """Composite DI surface: five leaf control protocols (no methods of its own).

    Implemented by the daemon aggregate / orchestrator; consumed by the
    service capability so it imports only from ``*_protocol`` (HOW-TO).
    """


__all__ = [
    'DaemonName',
    'DaemonOp',
    'DaemonStatus',
    'DaemonUnit',
    'ExitCode',
    'IDaemonControlProtocol',
    'IDaemonLogsProtocol',
    'IDaemonProtocol',
    'IDaemonRestartProtocol',
    'IDaemonStartProtocol',
    'IDaemonStatusProtocol',
    'IDaemonStopProtocol',
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonName": DaemonName,
    "DaemonOp": DaemonOp,
    "DaemonStatus": DaemonStatus,
    "DaemonUnit": DaemonUnit,
    "ExitCode": ExitCode,
    "IDaemonControlProtocol": IDaemonControlProtocol,
    "IDaemonLogsProtocol": IDaemonLogsProtocol,
    "IDaemonProtocol": IDaemonProtocol,
    "IDaemonRestartProtocol": IDaemonRestartProtocol,
    "IDaemonStartProtocol": IDaemonStartProtocol,
    "IDaemonStatusProtocol": IDaemonStatusProtocol,
    "IDaemonStopProtocol": IDaemonStopProtocol,
}
