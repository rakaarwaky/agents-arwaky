"""Root composition — tools feature wiring + lifecycle aggregate.

The AES root layer is the only layer allowed to import ``capabilities*``;
this module centralises the tool_id -> adapter-instance mapping so that
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

from modules.shared.src.utility_paths import repo_root
from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
from modules.tools.src.utility_anytype_adapter import AnytypeAdapter, AnytypeDaemonAdapter
from modules.tools.src.utility_blender_adapter import BlenderAdapter
from modules.tools.src.utility_codegraph_adapter import CodegraphAdapter
from modules.tools.src.utility_context7_adapter import Context7Adapter
from modules.tools.src.utility_fetch_adapter import FetchAdapter
from modules.tools.src.utility_lint_adapter import LintAdapter
from modules.tools.src.utility_mnemosyne_adapter import MnemosyneAdapter
from modules.tools.src.utility_ninerouter_adapter import NinerouterAdapter
from modules.tools.src.utility_ponytail_adapter import PonytailAdapter
from modules.tools.src.utility_qwen_web_adapter import QwenWebAdapter
from modules.tools.src.utility_vision_adapter import VisionAdapter
from modules.tools.src.utility_workspace_adapter import WorkspaceAdapter

# Root is the only layer allowed to import capabilities_* (AES201 rule 8):
# the four verb capabilities are constructed here and injected into the
# agent orchestrator (which must stay capabilities-free). Importing them
# here also wires them for the AES503 orphan check.
from modules.tools.src.capabilities_tools_installer import InstallerCapability
from modules.tools.src.capabilities_tools_runner import RunnerCapability
from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
from modules.tools.src.capabilities_tools_updater import UpdaterCapability
from modules.tools.src.contract_tools_aggregate import IToolsAggregate

#: tool_id -> adapter instance (root composition data; each adapter is a
#: stateless plain class — no per-registry state, constructed once here).
TOOLS_REGISTRY: dict[str, object] = {
    "anytype": AnytypeAdapter(),
    "anytype-daemon": AnytypeDaemonAdapter(),
    "blender": BlenderAdapter(),
    "codegraph": CodegraphAdapter(),
    "context7": Context7Adapter(),
    "fetch": FetchAdapter(),
    "lint": LintAdapter(),
    "mnemosyne": MnemosyneAdapter(),
    "9router": NinerouterAdapter(),
    "ponytail": PonytailAdapter(),
    "qwen-web": QwenWebAdapter(),
    "vision": VisionAdapter(),
    "workspace": WorkspaceAdapter(),
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
