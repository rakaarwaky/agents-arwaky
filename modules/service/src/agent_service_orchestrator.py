"""Service agent orchestrator — thin aggregate over the service manager."""
from __future__ import annotations

from modules.shared.src.contract_service_aggregate import IServiceAggregate
from modules.shared.src.contract_service_protocol import IServiceProtocol
from modules.shared.src.taxonomy_service_vo import (
    TARGET_ALL,
    TARGET_OMNIROUTE,
    ExitCode,
    ServiceOp,
    ServiceTarget,
)


# ─── Block 1: Class Definition & Constructor ──────────────
class ServiceOrchestrator(IServiceAggregate):
    """Delegates every service action to the injected IServiceProtocol."""

    def __init__(self, manager: IServiceProtocol) -> None:
        self._manager = manager

    # ─── Block 2: Aggregate Method Implementation ──────────
    def status(self) -> ExitCode:
        return ExitCode(int(self._manager.execute(ServiceOp("status"))))

    def start(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        return ExitCode(int(self._manager.execute(ServiceOp("start"), target)))

    def stop(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        return ExitCode(int(self._manager.execute(ServiceOp("stop"), target)))

    def restart(self, target: ServiceTarget = TARGET_ALL) -> ExitCode:
        return ExitCode(int(self._manager.execute(ServiceOp("restart"), target)))

    def logs(self, target: ServiceTarget = TARGET_OMNIROUTE) -> ExitCode:
        return ExitCode(int(self._manager.execute(ServiceOp("logs"), target)))

    def help(self) -> ExitCode:
        return ExitCode(int(self._manager.execute(ServiceOp("help"))))

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    def __repr__(self) -> str:
        return "ServiceOrchestrator()"


__all__ = ["ExitCode", "ServiceTarget"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "ServiceTarget": ServiceTarget}
