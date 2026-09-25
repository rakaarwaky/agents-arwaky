"""Root composition — tools feature wiring + lifecycle aggregate.

The AES root layer is the only layer allowed to import ``capabilities*``;
this module centralises the tool_id -> adapter-unit mapping so that
``agent_tools_orchestrator`` stays adapter-free (AES201 rule 8). Adapters
carry no per-registry state: each unit is constructed once here and shared
across orchestrator instances; the daemon aggregate is passed to
``install`` explicitly, never held on the adapter.

Every tool id lives in a sibling capability module — the nine
config-driven providers (blender / vision / qwen-web / mnemosyne /
workspace / codegraph / context7 / fetch / ponytail) plus anytype, lint,
and 9router — each exporting ``ADAPTER_UNITS``; all are merged into the
single ``TOOLS_REGISTRY`` below.

The daemon aggregate is imported lazily inside the factory so that importing
``modules.tools`` never forces a sibling daemon import at module load.
"""
from __future__ import annotations

from modules.shared.src.contract_tools_aggregate import IToolsAggregate
from modules.shared.src.utility_paths_resolver import repo_root
from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

# Root is the only layer allowed to import capabilities_* (AES201 rule 8):
# every adapter capability is constructed here and injected into the
# agent orchestrator (which must stay capabilities-free). Importing them
# here also wires them for the AES503 orphan check.
from modules.tools.src.capabilities_tools_adapter import ToolAdapterFacade
from modules.tools.src.capabilities_tools_anytype_adapter import (
    ADAPTER_UNITS as _ANYTYPE_UNITS,
)
from modules.tools.src.capabilities_tools_blender_adapter import (
    ADAPTER_UNITS as _BLENDER_UNITS,
)
from modules.tools.src.capabilities_tools_codegraph_adapter import (
    ADAPTER_UNITS as _CODEGRAPH_UNITS,
)
from modules.tools.src.capabilities_tools_context7_adapter import (
    ADAPTER_UNITS as _CONTEXT7_UNITS,
)
from modules.tools.src.capabilities_tools_fetch_adapter import (
    ADAPTER_UNITS as _FETCH_UNITS,
)
from modules.tools.src.capabilities_tools_installer import InstallerCapability
from modules.tools.src.capabilities_tools_lint_adapter import (
    ADAPTER_UNITS as _LINT_UNITS,
)
from modules.tools.src.capabilities_tools_mnemosyne_adapter import (
    ADAPTER_UNITS as _MNEMOSYNE_UNITS,
)
from modules.tools.src.capabilities_tools_ninerouter_adapter import (
    ADAPTER_UNITS as _NINEROUTER_UNITS,
)
from modules.tools.src.capabilities_tools_ponytail_adapter import (
    ADAPTER_UNITS as _PONYTAIL_UNITS,
)
from modules.tools.src.capabilities_tools_qwen_web_adapter import (
    ADAPTER_UNITS as _QWEN_WEB_UNITS,
)
from modules.tools.src.capabilities_tools_runner import RunnerCapability
from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
from modules.tools.src.capabilities_tools_updater import UpdaterCapability
from modules.tools.src.capabilities_tools_vision_adapter import (
    ADAPTER_UNITS as _VISION_UNITS,
)
from modules.tools.src.capabilities_tools_workspace_adapter import (
    ADAPTER_UNITS as _WORKSPACE_UNITS,
)

#: tool_id -> adapter unit (root composition data; each unit is a
#: stateless `AdapterUnit` VO of action functions).
TOOLS_REGISTRY: dict[str, object] = {
    **_ANYTYPE_UNITS,
    **_BLENDER_UNITS,
    **_CODEGRAPH_UNITS,
    **_CONTEXT7_UNITS,
    **_FETCH_UNITS,
    **_LINT_UNITS,
    **_MNEMOSYNE_UNITS,
    **_NINEROUTER_UNITS,
    **_PONYTAIL_UNITS,
    **_QWEN_WEB_UNITS,
    **_VISION_UNITS,
    **_WORKSPACE_UNITS,
}


def create_tools_feature(root=None) -> IToolsAggregate:
    """Fully-wired tools feature aggregate (composition-time wiring, root layer).

    The daemon aggregate is imported lazily so that importing ``modules.tools``
    does not force a sibling daemon import at module load.
    """
    from modules.daemon.src.root_daemon_container import create_daemon_feature

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
