"""Root composition — updater registry wiring per-tool adapters.

The AES root layer is the only layer allowed to import adapter classes;
this module centralises the manifest id -> adapter-class mapping so that
``agent_updater_orchestrator`` stays adapter-free (AES201 rule 8).

The 1:1 shared-domain principle: each manifest tool id maps to exactly one
leaf adapter. The `9router` id keeps the repo's `ninerouter` naming
convention (tool id starts with a digit; file/class names use `ninerouter`).

`anytype-daemon` maps to its own adapter (the container/daemon half); the
`anytype` id's adapter owns the mcp + daemon rebuild for the `anytype` entry.
"""
from __future__ import annotations

from modules.updater.src.agent_updater_orchestrator import UpdaterOrchestrator
from modules.updater.src.utility_anytype_daemon_updater import AnytypeDaemonUpdaterAdapter
from modules.updater.src.utility_anytype_updater import AnytypeUpdaterAdapter
from modules.updater.src.utility_blender_updater import BlenderUpdaterAdapter
from modules.updater.src.utility_codegraph_updater import CodegraphUpdaterAdapter
from modules.updater.src.utility_context7_updater import Context7UpdaterAdapter
from modules.updater.src.utility_fetch_updater import FetchUpdaterAdapter
from modules.updater.src.utility_lint_updater import LintUpdaterAdapter
from modules.updater.src.utility_mnemosyne_updater import MnemosyneUpdaterAdapter
from modules.updater.src.utility_ninerouter_updater import NinerouterUpdaterAdapter
from modules.updater.src.utility_ponytail_updater import PonytailUpdaterAdapter
from modules.updater.src.utility_qwen_web_updater import QwenWebUpdaterAdapter
from modules.updater.src.utility_vision_updater import VisionUpdaterAdapter
from modules.updater.src.utility_workspace_updater import WorkspaceUpdaterAdapter

#: manifest id -> per-tool adapter class (root composition data).
UPDATER_ADAPTERS: dict[str, type] = {
    "anytype": AnytypeUpdaterAdapter,
    "anytype-daemon": AnytypeDaemonUpdaterAdapter,
    "blender": BlenderUpdaterAdapter,
    "codegraph": CodegraphUpdaterAdapter,
    "context7": Context7UpdaterAdapter,
    "fetch": FetchUpdaterAdapter,
    "lint": LintUpdaterAdapter,
    "mnemosyne": MnemosyneUpdaterAdapter,
    "9router": NinerouterUpdaterAdapter,
    "ponytail": PonytailUpdaterAdapter,
    "qwen-web": QwenWebUpdaterAdapter,
    "vision": VisionUpdaterAdapter,
    "workspace": WorkspaceUpdaterAdapter,
}


def build_updater_orchestrator(root=None) -> UpdaterOrchestrator:
    """Instantiate the single orchestrator with the full adapter registry.

    Sets the orchestrator's class-level ``_ADAPTERS`` mapping and returns a
    configured instance. The runner's ToolOrchestrator calls
    ``updater.update(spec)`` which delegates to this orchestrator.
    """
    UpdaterOrchestrator._ADAPTERS = dict(UPDATER_ADAPTERS)
    return UpdaterOrchestrator(root=root)
