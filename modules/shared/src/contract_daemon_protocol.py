"""Daemon-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_daemon_vo import DaemonStatus, ExitCode


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


__all__ = ['DaemonStatus', 'ExitCode', 'IDaemonProtocol']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"DaemonStatus": DaemonStatus, "ExitCode": ExitCode, "IDaemonProtocol": IDaemonProtocol}
