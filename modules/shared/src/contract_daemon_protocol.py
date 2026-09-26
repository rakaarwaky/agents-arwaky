"""Daemon-domain protocol contract (capability ABC).

Pure capability ABC: one abstract method per daemon operation the managers
expose. Consumers never see this method list — the aggregate dispatches to
it via its single ``execute`` entry point.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import (
    DaemonStatus,
    DaemonUnit,
    ExitCode,
)


class IDaemonProtocol(ABC):
    """Capability contract for one daemon manager: one method per operation."""

    @abstractmethod
    def start(self) -> ExitCode:
        """Start the daemon and wait for readiness. Return the exit code."""
        ...

    @abstractmethod
    def stop(self) -> ExitCode:
        """Stop the running daemon. Return the exit code."""
        ...

    @abstractmethod
    def restart(self) -> ExitCode:
        """Restart the daemon, waiting for readiness after the stop. Return the exit code."""
        ...

    @abstractmethod
    def status(self) -> DaemonStatus:
        """Probe process, systemd, and API state. Return the health snapshot."""
        ...

    @abstractmethod
    def logs(self) -> ExitCode:
        """Show the daemon's recent logs. Return the exit code."""
        ...

    @abstractmethod
    def install_unit(self, unit: DaemonUnit) -> ExitCode:
        """Install and enable the systemd user unit *unit*. Return the exit code."""
        ...

    @abstractmethod
    def remove_unit(self, unit: DaemonUnit) -> ExitCode:
        """Disable and remove the systemd user unit *unit*. Return the exit code."""
        ...

    @abstractmethod
    def unit_status(self, unit: DaemonUnit) -> ExitCode:
        """Report the systemd state of *unit*. Return the exit code."""
        ...


__all__ = [
    "DaemonStatus",
    "DaemonUnit",
    "ExitCode",
    "IDaemonProtocol",
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonStatus": DaemonStatus,
    "DaemonUnit": DaemonUnit,
    "ExitCode": ExitCode,
    "IDaemonProtocol": IDaemonProtocol,
}
