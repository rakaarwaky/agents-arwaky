"""Root composition — uninstaller registry wiring per-tool capabilities.

The AES root layer is the only layer allowed to import `capabilities*`;
this module centralises the tool_id -> uninstaller-class mapping so that
`agent_uninstaller_orchestrator` stays capability-free (AES201 rule 8).
"""
from __future__ import annotations

from modules.uninstaller.src.capabilities_anytype_daemon_uninstaller import (
    AnytypeDaemonUninstaller,
)
from modules.uninstaller.src.capabilities_blender_uninstaller import BlenderUninstaller
from modules.uninstaller.src.capabilities_codegraph_uninstaller import CodegraphUninstaller
from modules.uninstaller.src.capabilities_context7_uninstaller import Context7Uninstaller
from modules.uninstaller.src.capabilities_fetch_mcp_uninstaller import FetchMcpUninstaller
from modules.uninstaller.src.capabilities_lint_uninstaller import LintUninstaller
from modules.uninstaller.src.capabilities_mnemosyne_uninstaller import MnemosyneUninstaller
from modules.uninstaller.src.capabilities_ninerouter_uninstaller import NinerouterUninstaller
from modules.uninstaller.src.capabilities_ponytail_uninstaller import PonytailUninstaller
from modules.uninstaller.src.capabilities_qwen_web_uninstaller import QwenWebUninstaller
from modules.uninstaller.src.capabilities_vision_uninstaller import VisionUninstaller
from modules.uninstaller.src.capabilities_workspace_uninstaller import WorkspaceUninstaller

#: tool_id -> concrete per-tool uninstaller class (root composition data).
UNINSTALLER_REGISTRY: dict[str, type] = {
    "anytype": AnytypeDaemonUninstaller,
    "anytype-daemon": AnytypeDaemonUninstaller,
    "blender": BlenderUninstaller,
    "codegraph": CodegraphUninstaller,
    "context7": Context7Uninstaller,
    "fetch": FetchMcpUninstaller,
    "lint": LintUninstaller,
    "mnemosyne": MnemosyneUninstaller,
    "9router": NinerouterUninstaller,
    "ponytail": PonytailUninstaller,
    "qwen-web": QwenWebUninstaller,
    "vision": VisionUninstaller,
    "workspace": WorkspaceUninstaller,
}
