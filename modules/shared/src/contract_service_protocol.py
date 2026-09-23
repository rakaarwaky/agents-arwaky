"""Service-domain protocol contract (capability ABC)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from modules.shared.src.taxonomy_service_vo import (
    TARGET_ALL,
    ExitCode,
    ServiceOp,
    ServiceTarget,
)


class IServiceProtocol(ABC):
    """Capability contract for the unified service manager."""

    @abstractmethod
    def execute(self, op: ServiceOp, unit: ServiceTarget = TARGET_ALL) -> ExitCode:
        """Run one service operation under *op*; return exit code.

        Args:
            op: Operation token — `status`, `start`, `stop`, `restart`,
                `logs`, or `help`.
            unit: Target unit/daemon(s) the op applies to.
        """
        ...


__all__ = ['ExitCode', 'IServiceProtocol', 'ServiceOp', 'ServiceTarget']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "IServiceProtocol": IServiceProtocol, "ServiceOp": ServiceOp, "ServiceTarget": ServiceTarget}
