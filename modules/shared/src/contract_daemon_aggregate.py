"""Daemon-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonStatus,
    DaemonUnit,
    ExitCode,
)


class IDaemonAggregate(ABC):
    """Aggregate routing daemon lifecycle, enumeration, and unit actions."""

    @abstractmethod
    def list_known(self) -> tuple[DaemonName, ...]:
        """Canonical daemon ids the orchestrator manages."""
        ...
    @abstractmethod
    def start(self, name: DaemonName) -> ExitCode:
        """Start the named daemon."""
        ...
    @abstractmethod
    def stop(self, name: DaemonName) -> ExitCode:
        """Stop the named daemon."""
        ...
    @abstractmethod
    def restart(self, name: DaemonName) -> ExitCode:
        """Restart the named daemon."""
        ...
    @abstractmethod
    def status(self, name: DaemonName) -> DaemonStatus:
        """Status snapshot for the named daemon."""
        ...
    @abstractmethod
    def logs(self, name: DaemonName) -> ExitCode:
        """Tail logs of the named daemon."""
        ...
    @abstractmethod
    def install_unit(self, unit: DaemonUnit) -> ExitCode:
        """Install the daemon's systemd user unit."""
        ...
    @abstractmethod
    def remove_unit(self, unit: DaemonUnit) -> ExitCode:
        """Remove the daemon's systemd user unit."""
        ...
    @abstractmethod
    def unit_status(self, unit: DaemonUnit) -> ExitCode:
        """Report install/active state of the daemon's systemd user unit."""
        ...

__all__ = ['DaemonName', 'DaemonStatus', 'DaemonUnit', 'ExitCode', 'IDaemonAggregate']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonName": DaemonName,
    "DaemonStatus": DaemonStatus,
    "DaemonUnit": DaemonUnit,
    "ExitCode": ExitCode,
    "IDaemonAggregate": IDaemonAggregate,
}
