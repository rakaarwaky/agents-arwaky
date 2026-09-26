"""Daemon surface — CLI adapters for aa anytype / aa 9router.

The 8 shared daemon operations go through the aggregate's single ``execute``;
the capability-specific verbs (models, auth-*, space-*, help) live on the
manager itself and are called there, since no other daemon implements them.
Both dependencies are constructed by the composition root and injected.
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
from modules.shared.src.contract_daemon_protocol import IDaemonProtocol
from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonOp,
    DaemonOutcome,
    DaemonRequest,
    DaemonResponse,
    DaemonUnit,
)

#: factory name -> manager callable, injected by the composition root.
_MANAGER_FACTORY: dict[str, Callable[[], IDaemonProtocol]] = {}

#: Request ops the shared contract owns; the agent dispatches each one.
_AGGREGATE_OPS = frozenset(
    {"start", "stop", "restart", "status", "logs", "install_unit", "remove_unit", "unit_status"}
)

#: Ops that need the manager's unit filename in the request.
_UNIT_OPS = frozenset({"install_unit", "remove_unit", "unit_status"})

#: CLI verb -> aggregate request op, for the shared contract ops.
_OPS: dict[str, str] = {
    "start": "start",
    "stop": "stop",
    "restart": "restart",
    "status": "status",
    "logs": "logs",
    "service-install": "install_unit",
    "service-status": "unit_status",
    "service-uninstall": "remove_unit",
}

#: CLI verb -> capability-specific manager method, for the verbs no other daemon shares.
_LOCAL_OPS: dict[str, str] = {
    "help": "help",
    "models": "models",
    "auth-create": "auth_create",
    "auth-key": "auth_key",
    "space-join": "space_join",
    "space-list": "space_list",
}

#: Default argument for a capability-specific verb that takes a name.
_DEFAULT_ARG: dict[str, str] = {
    "auth_create": "agent",
    "auth_key": "arwaky-agent-key",
    "space_join": "",
}


def register_manager_factory(name: str, factory: Callable[[], IDaemonProtocol]) -> None:
    """Register a manager factory for *name* (composition root only)."""
    _MANAGER_FACTORY[name] = factory


def _manager(name: str) -> IDaemonProtocol:
    factory = _MANAGER_FACTORY.get(name)
    if factory is None:
        raise RuntimeError(f"no daemon manager factory registered for {name!r}")
    return factory()


def _dispatch(
    orch: IDaemonAggregate,
    mgr: IDaemonProtocol,
    args: list[str],
    *,
    name: DaemonName,
    unit: DaemonUnit,
    label: str,
) -> int:
    """Route the CLI verb to the aggregate op or the capability-specific method."""
    if not args or args[0] in ("help", "-h", "--help"):
        return int(mgr.help())
    action = args[0]
    rest = args[1:]
    op = _OPS.get(action)
    if op is not None:
        request = DaemonRequest(
            DaemonOp(op),
            name=name,
            unit=unit if op in _UNIT_OPS else None,
        )
        return _exit_code(orch.execute(request))
    local = _LOCAL_OPS.get(action)
    if local is None:
        print(f"Unknown {label} command: {action}", file=sys.stderr)
        return int(mgr.help())
    return int(_local_call(mgr, local, rest))


def _local_call(mgr: IDaemonProtocol, method: str, rest: list[str]) -> int:
    """Invoke a capability-specific manager method, keeping the legacy defaults."""
    if method in _DEFAULT_ARG:
        return int(getattr(mgr, method)(rest[0] if rest else _DEFAULT_ARG[method]))
    return int(getattr(mgr, method)())


def _exit_code(response: DaemonResponse) -> int:
    """Render an aggregate response as a process exit code."""
    if response.status is not None:
        return 0 if response.status.ok else 1
    if response.exit_code is not None:
        return response.exit_code
    return 0 if response.success else 1


def cmd_9router(
    args: list[str],
    orch: IDaemonAggregate | None = None,
    manager: IDaemonProtocol | None = None,
) -> int:
    """aa 9router <command> — start|stop|restart|status|logs|models|service-*|help."""
    return _dispatch(
        orch,
        manager or _manager("9router"),
        args,
        name=DaemonName("9router"),
        unit=DaemonUnit("9router.service"),
        label="9router",
    )


def cmd_anytype(
    args: list[str],
    orch: IDaemonAggregate | None = None,
    manager: IDaemonProtocol | None = None,
) -> int:
    """aa anytype <command> — start|stop|restart|status|logs|auth-*|space-*|service-*|help."""
    return _dispatch(
        orch,
        manager or _manager("anytype"),
        args,
        name=DaemonName("anytype"),
        unit=DaemonUnit("anytype-daemon.service"),
        label="anytype",
    )


class DaemonAction(IDaemonAggregate):
    """Aggregate implementor wrapping another aggregate (surface-layer facade)."""

    def __init__(self, agg: IDaemonAggregate) -> None:
        """Store the underlying daemon aggregate for delegation."""
        self._agg = agg

    def execute(self, request: DaemonRequest) -> DaemonOutcome:
        """Delegate the request to the wrapped aggregate unchanged."""
        return self._agg.execute(request)


__all__ = [
    "DaemonAction",
    "DaemonName",
    "DaemonOp",
    "DaemonOutcome",
    "DaemonRequest",
    "DaemonResponse",
    "DaemonUnit",
    "cmd_anytype",
    "cmd_9router",
    "register_manager_factory",
]
