"""Root composition — tools feature wiring + lifecycle aggregate.

The AES root layer is the only layer allowed to import ``capabilities*``;
this module centralises the tool_id -> adapter-module mapping so that
``agent_tools_orchestrator`` stays adapter-free (AES201 rule 8). Adapters
carry no per-registry state: each is constructed once here and shared
across orchestrator instances; the daemon aggregate is passed to
``install`` explicitly, never held on the adapter.

Daemon-backed adapters (9router/anytype/anytype-daemon) receive the daemon
aggregate here, preserving the pre-existing feature-to-feature delegation
indirection.

The daemon aggregate is imported lazily inside the factory so that importing
``modules.tools`` never forces a sibling daemon import at module load.
"""
from __future__ import annotations

import modules.tools.src.capabilities_tools_adapter as _god
from modules.shared.src.contract_tools_aggregate import IToolsAggregate
from modules.shared.src.taxonomy_tools_vo import AdapterUnit
from modules.shared.src.utility_paths_resolver import repo_root
from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

# Root is the only layer allowed to import capabilities_* (AES201 rule 8):
# the four action capabilities are constructed here and injected into the
# agent orchestrator (which must stay capabilities-free). Importing them
# here also wires them for the AES503 orphan check.
from modules.tools.src.capabilities_tools_installer import InstallerCapability
from modules.tools.src.capabilities_tools_runner import RunnerCapability
from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
from modules.tools.src.capabilities_tools_updater import UpdaterCapability

#: tool_id -> adapter unit (root composition data; each unit is a
#: stateless `AdapterUnit` VO of action functions living in the god-object
#: `capabilities_tools_adapter`). The `anytype-daemon` id routes its
#: actions to the `anytype_daemon_*` leaf functions via a unit object.
_ANYTYPE_DAEMON = AdapterUnit(
    satisfied=_god.anytype_daemon_satisfied,
    install=_god.anytype_daemon_install,
    is_pin_satisfied=_god.anytype_daemon_is_pin_satisfied,
    update=_god.anytype_daemon_update,
    owned_paths=_god.anytype_daemon_owned_paths,
)

# AES404 (P0-1 follow-up): 9router and qwen-web now expose their actions as
# module-level functions (stateless utility layer) like the other adapters,
# so they are registered directly — no instance or namespace wrapper.
# The `is_daemon` flag that lived on NinerouterAdapter is no longer needed:
# daemon behaviour is driven by DAEMON_TOOL_IDS in taxonomy_tools_constant.

TOOLS_REGISTRY: dict[str, object] = {
    "anytype": _god._ADAPTER_UNITS["anytype"],
    "anytype-daemon": _ANYTYPE_DAEMON,
    "blender": _god._ADAPTER_UNITS["blender"],
    "codegraph": _god._ADAPTER_UNITS["codegraph"],
    "context7": _god._ADAPTER_UNITS["context7"],
    "fetch": _god._ADAPTER_UNITS["fetch"],
    "lint": _god._ADAPTER_UNITS["lint"],
    "mnemosyne": _god._ADAPTER_UNITS["mnemosyne"],
    "9router": _god._ADAPTER_UNITS["9router"],
    "ponytail": _god._ADAPTER_UNITS["ponytail"],
    "qwen-web": _god._ADAPTER_UNITS["qwen-web"],
    "vision": _god._ADAPTER_UNITS["vision"],
    "workspace": _god._ADAPTER_UNITS["workspace"],
}


def create_tools_feature(root=None) -> IToolsAggregate:
    """Fully-wired tools feature aggregate (composition-time wiring, root layer).

    The daemon aggregate is imported lazily so that importing ``modules.tools``
    does not force a sibling daemon import at module load.
    """
    from modules.daemon.src.root_daemon_container import create_daemon_feature
    from modules.tools.src.capabilities_tools_adapter import ToolAdapterFacade

    daemons = create_daemon_feature()
    resolved = root or repo_root()
    # P1-7: the adapter facade is the single API pipeline over all 13 leaf
    # adapters + shared mechanics; wired here and injected into the action
    # capabilities (dependency inversion: capabilities depend on the
    # IToolsProtocol contract, not the concrete ToolAdapterFacade).
    adapter_facade = ToolAdapterFacade(
        registry=TOOLS_REGISTRY, daemons=daemons, root=resolved
    )
    installer = InstallerCapability(root=resolved, daemons=daemons, adapter_facade=adapter_facade)
    updater = UpdaterCapability(root=resolved, adapter_facade=adapter_facade)
    uninstaller = UninstallerCapability(daemons=daemons)
    runner = RunnerCapability(root=resolved)
    return ToolsOrchestrator(
        registry=TOOLS_REGISTRY,
        root=resolved,
        daemons=daemons,
        installer=installer,
        updater=updater,
        uninstaller=uninstaller,
        runner=runner,
        adapter_facade=adapter_facade,
    )


__all__ = ["TOOLS_REGISTRY", "create_tools_feature"]
