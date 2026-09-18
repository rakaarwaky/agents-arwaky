"""Root composition — installer registry wiring per-tool capabilities.

The AES root layer is the only layer allowed to import ``capabilities*``;
this module centralises the tool_id -> installer-class mapping so that
``agent_installer_orchestrator`` stays capability-free (AES201 rule 8).
"""
from __future__ import annotations

from modules.daemon.src.root_daemon_container import create_daemon_feature
from modules.installer.src.capabilities_anytype_installer import AnytypeInstaller
from modules.installer.src.capabilities_blender_installer import BlenderInstaller
from modules.installer.src.capabilities_codegraph_installer import CodegraphInstaller
from modules.installer.src.capabilities_context7_installer import Context7Installer
from modules.installer.src.capabilities_fetch_installer import FetchInstaller
from modules.installer.src.capabilities_lint_installer import LintInstaller
from modules.installer.src.capabilities_mnemosyne_installer import MnemosyneInstaller
from modules.installer.src.capabilities_ninerouter_installer import NinerouterInstaller
from modules.installer.src.capabilities_ponytail_installer import PonytailInstaller
from modules.installer.src.capabilities_qwen_web_installer import QwenWebInstaller
from modules.installer.src.capabilities_skill_installer import SkillInstaller
from modules.installer.src.capabilities_vision_installer import VisionInstaller
from modules.installer.src.capabilities_workspace_installer import WorkspaceInstaller

#: tool_id -> concrete per-tool installer class (root composition data).
INSTALLER_REGISTRY: dict[str, type] = {
    # anytype-daemon is part of the merged anytype installer
    "anytype-daemon": AnytypeInstaller,
    "anytype": AnytypeInstaller,
    "blender": BlenderInstaller,
    "codegraph": CodegraphInstaller,
    "context7": Context7Installer,
    "fetch": FetchInstaller,
    "lint": LintInstaller,
    "mnemosyne": MnemosyneInstaller,
    "9router": NinerouterInstaller,
    "ponytail": PonytailInstaller,
    "qwen-web": QwenWebInstaller,
    "skill": SkillInstaller,
    "vision": VisionInstaller,
    "workspace": WorkspaceInstaller,
}

# Classes whose constructor takes the daemon aggregate (9router/anytype).
_DAEMON_TOOLS: frozenset[str] = frozenset({"9router", "anytype", "anytype-daemon"})


def build_installer_registry(root=None) -> dict[str, object]:
    """Instantiate every registered installer, injecting the daemon aggregate
    where the capability needs it (composition-time wiring, root layer)."""
    daemons = create_daemon_feature()
    return {
        tool_id: cls(root, daemons=daemons) if tool_id in _DAEMON_TOOLS else cls(root)
        for tool_id, cls in INSTALLER_REGISTRY.items()
    }
