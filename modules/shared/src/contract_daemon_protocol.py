"""Daemon-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import DaemonName, DaemonStatus, ExitCode


class IDaemonProtocol(ABC):
    """Capability contract for one daemon manager."""

    @abstractmethod
    def execute(
        self,
        op: str,
        name: str | None = None,
        unit: str | None = None,
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


class IDaemonControlProtocol(ABC):
    """Narrow multi-daemon control surface (start/stop/restart/status/logs).

    Implemented by the daemon aggregate / orchestrator; consumed by the
    service capability so it imports only from ``*_protocol`` (HOW-TO).
    """

    @abstractmethod
    def start(self, name: DaemonName) -> ExitCode: ...
    @abstractmethod
    def stop(self, name: DaemonName) -> ExitCode: ...
    @abstractmethod
    def restart(self, name: DaemonName) -> ExitCode: ...
    @abstractmethod
    def status(self, name: DaemonName) -> DaemonStatus: ...
    @abstractmethod
    def logs(self, name: DaemonName) -> ExitCode: ...


__all__ = ['DaemonName', 'DaemonStatus', 'ExitCode', 'IDaemonControlProtocol', 'IDaemonProtocol']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonName": DaemonName,
    "DaemonStatus": DaemonStatus,
    "ExitCode": ExitCode,
    "IDaemonControlProtocol": IDaemonControlProtocol,
    "IDaemonProtocol": IDaemonProtocol,
}
