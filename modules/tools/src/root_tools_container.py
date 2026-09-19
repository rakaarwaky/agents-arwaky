"""Root composition — tools feature wiring + lifecycle aggregate.

The AES root layer is the only layer allowed to import ``capabilities*``;
this module centralises the tool_id -> unified-adapter-class mapping so that
``agent_tools_orchestrator`` stays adapter-free (AES201 rule 8). Daemon-backed
adapters (9router/anytype/anytype-daemon) receive the daemon aggregate here,
preserving the pre-existing feature-to-feature delegation indirection.

The daemon aggregate is imported lazily inside the factory so that importing
``modules.tools`` never forces a sibling daemon import at module load.
"""
from __future__ import annotations

from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
from modules.tools.src.contract_tools_aggregate import IToolsAggregate
from modules.tools.src.utility_anytype_adapter import AnytypeAdapter
from modules.tools.src.utility_anytype_daemon_adapter import AnytypeDaemonAdapter
from modules.tools.src.utility_blender_adapter import BlenderAdapter
from modules.tools.src.utility_codegraph_adapter import CodegraphAdapter
from modules.tools.src.utility_context7_adapter import Context7Adapter
from modules.tools.src.utility_fetch_adapter import FetchAdapter
from modules.tools.src.utility_lint_adapter import LintAdapter
from modules.tools.src.utility_mnemosyne_adapter import MnemosyneAdapter
from modules.tools.src.utility_ninerouter_adapter import NinerouterAdapter
from modules.tools.src.utility_ponytail_adapter import PonytailAdapter
from modules.tools.src.utility_qwen_web_adapter import QwenWebAdapter
from modules.tools.src.utility_skill_adapter import SkillAdapter
from modules.tools.src.utility_vision_adapter import VisionAdapter
from modules.tools.src.utility_workspace_adapter import WorkspaceAdapter

#: tool_id -> concrete unified per-tool adapter class (root composition data).
TOOLS_REGISTRY: dict[str, type] = {
    "anytype": AnytypeAdapter,
    "anytype-daemon": AnytypeDaemonAdapter,
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


def create_tools_feature(root=None) -> IToolsAggregate:
    """Fully-wired tools feature aggregate (composition-time wiring, root layer).

    The daemon aggregate is imported lazily so that importing ``modules.tools``
    does not force a sibling daemon import at module load.
    """
    from modules.daemon.src.root_daemon_container import create_daemon_feature

    daemons = create_daemon_feature()
    return ToolsOrchestrator(registry=TOOLS_REGISTRY, root=root, daemons=daemons)


__all__ = ["TOOLS_REGISTRY", "create_tools_feature"]
