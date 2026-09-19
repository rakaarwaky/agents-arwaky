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

import modules.tools.src.utility_anytype_adapter as _anytype
import modules.tools.src.utility_blender_adapter as _blender
import modules.tools.src.utility_codegraph_adapter as _codegraph
import modules.tools.src.utility_context7_adapter as _context7
import modules.tools.src.utility_fetch_adapter as _fetch
import modules.tools.src.utility_lint_adapter as _lint
import modules.tools.src.utility_mnemosyne_adapter as _mnemosyne
import modules.tools.src.utility_ninerouter_adapter as _ninerouter
import modules.tools.src.utility_ponytail_adapter as _ponytail
import modules.tools.src.utility_qwen_web_adapter as _qwen_web
import modules.tools.src.utility_vision_adapter as _vision
import modules.tools.src.utility_workspace_adapter as _workspace
from modules.shared.src.utility_paths_resolver import repo_root
from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

# Root is the only layer allowed to import capabilities_* (AES201 rule 8):
# the four verb capabilities are constructed here and injected into the
# agent orchestrator (which must stay capabilities-free). Importing them
# here also wires them for the AES503 orphan check.
from modules.tools.src.capabilities_tools_installer import InstallerCapability
from modules.tools.src.capabilities_tools_runner import RunnerCapability
from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
from modules.tools.src.capabilities_tools_updater import UpdaterCapability
from modules.tools.src.contract_tools_aggregate import IToolsAggregate
from types import SimpleNamespace

#: tool_id -> adapter module (root composition data; each is a stateless
#: leaf of module-level verb functions). The `anytype-daemon` id routes its
#: verbs to the `daemon_*` leaf functions via a namespace object.
_ANYTYPE_DAEMON = SimpleNamespace(
    satisfied=_anytype.daemon_satisfied,
    install=_anytype.daemon_install,
    is_pin_satisfied=_anytype.daemon_is_pin_satisfied,
    update=_anytype.daemon_update,
    owned_paths=_anytype.daemon_owned_paths,
)

# AES404 (P0-1 follow-up): 9router and qwen-web now expose their verbs as
# module-level functions (stateless utility layer) like the other adapters,
# so they are registered directly — no instance or SimpleNamespace wrapper.
# The `is_daemon` flag that lived on NinerouterAdapter is no longer needed:
# daemon behaviour is driven by DAEMON_TOOL_IDS in taxonomy_tools_constant.

TOOLS_REGISTRY: dict[str, object] = {
    "anytype": _anytype,
    "anytype-daemon": _ANYTYPE_DAEMON,
    "blender": _blender,
    "codegraph": _codegraph,
    "context7": _context7,
    "fetch": _fetch,
    "lint": _lint,
    "mnemosyne": _mnemosyne,
    "9router": _ninerouter,
    "ponytail": _ponytail,
    "qwen-web": _qwen_web,
    "vision": _vision,
    "workspace": _workspace,
}


def create_tools_feature(root=None) -> IToolsAggregate:
    """Fully-wired tools feature aggregate (composition-time wiring, root layer).

    The daemon aggregate is imported lazily so that importing ``modules.tools``
    does not force a sibling daemon import at module load.
    """
    from modules.daemon.src.root_daemon_container import create_daemon_feature

    daemons = create_daemon_feature()
    resolved = root or repo_root()
    installer = InstallerCapability(root=resolved, daemons=daemons)
    updater = UpdaterCapability(root=resolved)
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
    )


__all__ = ["TOOLS_REGISTRY", "create_tools_feature"]
