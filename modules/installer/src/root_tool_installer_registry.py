"""Root composition — installer registry wiring per-tool adapters.

The AES root layer is the only layer allowed to import ``capabilities*``;
this module centralises the tool_id -> adapter-class mapping so that
``agent_installer_orchestrator`` stays adapter-free (AES201 rule 8).
Daemon-backed adapters (9router/anytype) receive the daemon aggregate here,
preserving the pre-existing feature-to-feature delegation indirection.
"""
from __future__ import annotations

from modules.daemon.src.root_daemon_container import create_daemon_feature
from modules.installer.src.agent_installer_orchestrator import InstallerOrchestrator
from modules.installer.src.utility_anytype_adapter import AnytypeAdapter
from modules.installer.src.utility_blender_adapter import BlenderAdapter
from modules.installer.src.utility_codegraph_adapter import CodegraphAdapter
from modules.installer.src.utility_context7_adapter import Context7Adapter
from modules.installer.src.utility_fetch_adapter import FetchAdapter
from modules.installer.src.utility_lint_adapter import LintAdapter
from modules.installer.src.utility_mnemosyne_adapter import MnemosyneAdapter
from modules.installer.src.utility_ninerouter_adapter import NinerouterAdapter
from modules.installer.src.utility_ponytail_adapter import PonytailAdapter
from modules.installer.src.utility_qwen_web_adapter import QwenWebAdapter
from modules.installer.src.utility_skill_adapter import SkillAdapter
from modules.installer.src.utility_vision_adapter import VisionAdapter
from modules.installer.src.utility_workspace_adapter import WorkspaceAdapter

#: tool_id -> concrete per-tool adapter class (root composition data).
INSTALLER_REGISTRY: dict[str, type] = {
    # anytype-daemon is part of the merged anytype adapter
    "anytype-daemon": AnytypeAdapter,
    "anytype": AnytypeAdapter,
    "blender": BlenderAdapter,
    "codegraph": CodegraphAdapter,
    "context7": Context7Adapter,
    "fetch": FetchAdapter,
    "lint": LintAdapter,
    "mnemosyne": MnemosyneAdapter,
    "9router": NinerouterAdapter,
    "ponytail": PonytailAdapter,
    "qwen-web": QwenWebAdapter,
    "skill": SkillAdapter,
    "vision": VisionAdapter,
    "workspace": WorkspaceAdapter,
}

#: Tool ids whose adapters receive the daemon aggregate at install time.
_DAEMON_TOOLS: frozenset[str] = frozenset({"9router", "anytype", "anytype-daemon"})


def build_installer_registry(root=None) -> InstallerOrchestrator:
    """Fully-wired installer orchestrator (composition-time wiring, root layer)."""
    daemons = create_daemon_feature()
    return InstallerOrchestrator(registry=INSTALLER_REGISTRY, root=root, daemons=daemons)


__all__ = ["INSTALLER_REGISTRY", "build_installer_registry"]
