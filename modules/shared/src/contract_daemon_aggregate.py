"""Daemon-domain aggregate contract (agent orchestrator ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.contract_daemon_protocol import IDaemonControlProtocol
from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonNames,
    DaemonStatus,
    DaemonUnit,
    ExitCode,
)


class IDaemonAggregate(IDaemonControlProtocol, ABC):
    """Aggregate routing daemon lifecycle, enumeration, and unit actions."""

    @abstractmethod
    def list_known(self) -> DaemonNames:
        """Canonical daemon ids the orchestrator manages."""
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


__all__ = ['DaemonName', 'DaemonNames', 'DaemonStatus', 'DaemonUnit', 'ExitCode', 'IDaemonAggregate']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonName": DaemonName,
    "DaemonNames": DaemonNames,
    "DaemonStatus": DaemonStatus,
    "DaemonUnit": DaemonUnit,
    "ExitCode": ExitCode,
    "IDaemonAggregate": IDaemonAggregate,
}
