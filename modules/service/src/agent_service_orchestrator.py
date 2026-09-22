"""Service agent orchestrator — thin aggregate over the service manager."""
from __future__ import annotations
from modules.shared.src.taxonomy_core_vo import Timestamp


from modules.service.src.contract_service_aggregate import IServiceAggregate
from modules.service.src.contract_service_protocol import IServiceManager


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
    def status(self) -> int:
        return self._manager.status()

    def start(self, target: str = "all") -> int:
        return self._manager.start(target)

    def stop(self, target: str = "all") -> int:
        return self._manager.stop(target)

    def restart(self, target: str = "all") -> int:
        return self._manager.restart(target)

    def logs(self, target: str = "omniroute") -> int:
        return self._manager.logs(target)

    # -- Block 3: Help --------------------------------------------------------------
    def help(self) -> int:
        return self._manager.help()

__all__ = ['Timestamp']

#

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {"Timestamp": Timestamp}
