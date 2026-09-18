"""Root composition — updater registry wiring per-tool capabilities.

The AES root layer is the only layer allowed to import ``capabilities*``;
this module centralises the tool_id -> updater-class mapping so that
``agent_updater_orchestrator`` stays capability-free (AES201 rule 8).
"""
from __future__ import annotations

from modules.daemon.src.root_daemon_container import create_daemon_feature
from modules.updater.src.capabilities_anytype_updater import AnytypeUpdater
from modules.updater.src.capabilities_blender_updater import BlenderUpdater
from modules.updater.src.capabilities_codegraph_updater import CodegraphUpdater
from modules.updater.src.capabilities_context7_updater import Context7Updater
from modules.updater.src.capabilities_fetch_updater import FetchUpdater
from modules.updater.src.capabilities_lint_updater import LintUpdater
from modules.updater.src.capabilities_mnemosyne_updater import MnemosyneUpdater
from modules.updater.src.capabilities_ninerouter_updater import NinerouterUpdater
from modules.updater.src.capabilities_ponytail_updater import PonytailUpdater
from modules.updater.src.capabilities_workspace_updater import WorkspaceUpdater

#: tool_id -> concrete per-tool updater class (root composition data).
UPDATER_REGISTRY: dict[str, type] = {
    "anytype": AnytypeUpdater,
    "anytype-daemon": AnytypeUpdater,
    "blender": BlenderUpdater,
    "codegraph": CodegraphUpdater,
    "context7": Context7Updater,
    "fetch": FetchUpdater,
    "lint": LintUpdater,
    "mnemosyne": MnemosyneUpdater,
    "9router": NinerouterUpdater,
    "ponytail": PonytailUpdater,
    "workspace": WorkspaceUpdater,
}

# Classes whose constructor takes the daemon aggregate (9router/anytype).
_DAEMON_TOOLS: frozenset[str] = frozenset({"9router", "anytype", "anytype-daemon"})


def build_updater_registry(root=None) -> dict[str, object]:
    """Instantiate every registered updater, injecting the daemon aggregate
    where the capability needs it (composition-time wiring, root layer)."""
    daemons = create_daemon_feature()
    return {
        tool_id: cls(root, daemons=daemons) if tool_id in _DAEMON_TOOLS else cls(root)
        for tool_id, cls in UPDATER_REGISTRY.items()
    }
