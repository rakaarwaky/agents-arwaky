"""Root composition — updater registry wiring per-tool capabilities.

The AES root layer is the only layer allowed to import `capabilities*`;
this module centralises the tool_id -> updater-class mapping so that
`agent_updater_orchestrator` stays capability-free (AES201 rule 8).
"""
from __future__ import annotations

from modules.updater.src.capabilities_anytype_updater import AnytypeUpdater
from modules.updater.src.capabilities_blender_updater import BlenderUpdater
from modules.updater.src.capabilities_codegraph_updater import CodegraphUpdater
from modules.updater.src.capabilities_context7_updater import Context7Updater
from modules.updater.src.capabilities_fetch_updater import FetchUpdater
from modules.updater.src.capabilities_lint_updater import LintUpdater
from modules.updater.src.capabilities_mnemosyne_updater import MnemosyneUpdater
from modules.updater.src.capabilities_ninerouter_updater import NinerouterUpdater
from modules.updater.src.capabilities_ponytail_updater import PonytailUpdater
from modules.updater.src.capabilities_qwen_web_updater import QwenWebUpdater
from modules.updater.src.capabilities_vision_updater import VisionUpdater
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
    "qwen-web": QwenWebUpdater,
    "vision": VisionUpdater,
    "workspace": WorkspaceUpdater,
}
