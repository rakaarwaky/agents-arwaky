"""Daemon-domain protocol contract (capability ABC).

Exactly one method per feature (`execute`). Consumers (service manager,
daemon surface) talk through this single dispatch; the aggregate layer
provides the richer export surface.
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


__all__ = [
    'DaemonName',
    'DaemonOp',
    'DaemonStatus',
    'DaemonUnit',
    'ExitCode',
    'IDaemonProtocol',
]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "DaemonName": DaemonName,
    "DaemonOp": DaemonOp,
    "DaemonStatus": DaemonStatus,
    "DaemonUnit": DaemonUnit,
    "ExitCode": ExitCode,
    "IDaemonProtocol": IDaemonProtocol,
}
