"""Service agent orchestrator — thin aggregate over the service manager."""
from __future__ import annotations

from modules.shared.src.contract_service_aggregate import IServiceAggregate
from modules.shared.src.contract_service_protocol import IServiceManager
from modules.shared.src.taxonomy_service_vo import ExitCode, ServiceTarget


class ServiceOrchestrator(IServiceAggregate):
    """Delegates every service verb to the injected IServiceManager.

    # Block 1: Constructor
    # Block 2: Verb delegation
    # Block 3: Help
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(self, manager: IServiceManager) -> None:
        self._manager = manager

    # -- Block 2: Verb delegation ------------------------------------------------
    def status(self) -> ExitCode:
        return ExitCode(self._manager.status())

    def start(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        return ExitCode(self._manager.start(target))

    def stop(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        return ExitCode(self._manager.stop(target))

    def restart(self, target: ServiceTarget = ServiceTarget("all")) -> ExitCode:
        return ExitCode(self._manager.restart(target))

    def logs(self, target: ServiceTarget = ServiceTarget("omniroute")) -> ExitCode:
        return ExitCode(self._manager.logs(target))

    # -- Block 3: Help --------------------------------------------------------------
    def help(self) -> ExitCode:
        return ExitCode(self._manager.help())

__all__ = ['ExitCode', 'ServiceTarget']

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"ExitCode": ExitCode, "ServiceTarget": ServiceTarget}
