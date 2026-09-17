"""Service manager capability — unified control over the daemons."""
from __future__ import annotations

from modules.daemon.src.capabilities_daemon_anytype import AnytypeDaemonManager
from modules.daemon.src.capabilities_daemon_podman import PodmanDaemonManager
from modules.shared.src.daemon.contract_daemon_protocol import IDaemonManager
from modules.shared.src.service.contract_service_protocol import IServiceManager


class ServiceManager(IServiceManager):
    """Status / start / stop / restart / logs across the managed daemons.

    Subprocess calls to the daemon modules are replaced by injected
    IDaemonManager instances.

    # Block 1: Constructor (daemon injection)
    # Block 2: Target routing
    # Block 3: Service verbs
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        ninerouter: IDaemonManager,
        anytype: IDaemonManager,
    ) -> None:
        self._ninerouter = ninerouter
        self._anytype = anytype

    # -- Block 2: Target routing -------------------------------------------------
    def _targets(self, target: str) -> tuple[bool, bool]:
        do_ninerouter = target in ("9router", "ninerouter", "all")
        do_anytype = target in ("anytype", "all")
        return do_ninerouter, do_anytype

    # -- Block 3: Service verbs ---------------------------------------------------
    def status(self) -> int:
        print("=========== 9Router ===========")
        self._ninerouter.status()
        print()
        print("=========== Anytype ===========")
        self._anytype.status()
        return 0

    def start(self, target: str = "all") -> int:
        do_ninerouter, do_anytype = self._targets(target)
        if do_ninerouter:
            self._ninerouter.start()
        if do_anytype:
            self._anytype.start()
        return 0

    def stop(self, target: str = "all") -> int:
        do_ninerouter, do_anytype = self._targets(target)
        if do_ninerouter:
            self._ninerouter.stop()
        if do_anytype:
            self._anytype.stop()
        return 0

    def restart(self, target: str = "all") -> int:
        do_ninerouter, do_anytype = self._targets(target)
        if do_ninerouter:
            self._ninerouter.restart()
        if do_anytype:
            self._anytype.restart()
        return 0

    def logs(self, target: str = "9router") -> int:
        if target in ("9router", "ninerouter"):
            return self._ninerouter.logs()
        if target == "anytype":
            return self._anytype.logs()
        print("Usage: aa service logs <9router|anytype>")
        return 1

    def help(self) -> int:
        print("Usage: aa service <status|start|stop|restart|logs> [9router|anytype|all]")
        return 0
