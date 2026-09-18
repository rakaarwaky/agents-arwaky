"""Root composition — runner registry wiring per-tool capabilities.

The AES root layer is the only layer allowed to import `capabilities*`;
this module centralises the tool_id -> runner-class mapping so that
`agent_runner_orchestrator` stays capability-free (AES201 rule 8).
"""
from __future__ import annotations

from modules.runner.src.capabilities_anytype_runner import AnytypeRunner
from modules.runner.src.capabilities_anytype_daemon_runner import AnytypeDaemonRunner
from modules.runner.src.capabilities_blender_runner import BlenderRunner
from modules.runner.src.capabilities_codegraph_runner import CodegraphRunner
from modules.runner.src.capabilities_context7_runner import Context7Runner
from modules.runner.src.capabilities_fetch_runner import FetchRunner
from modules.runner.src.capabilities_lint_runner import LintRunner
from modules.runner.src.capabilities_mnemosyne_runner import MnemosyneRunner
from modules.runner.src.capabilities_ninerouter_runner import NinerouterRunner
from modules.runner.src.capabilities_ponytail_runner import PonytailRunner
from modules.runner.src.capabilities_qwen_web_runner import QwenWebRunner
from modules.runner.src.capabilities_skill_runner import SkillRunner
from modules.runner.src.capabilities_vision_runner import VisionRunner
from modules.runner.src.capabilities_workspace_runner import WorkspaceRunner

#: tool_id -> concrete per-tool runner class (root composition data).
RUNNER_REGISTRY: dict[str, type] = {
    # anytype-daemon is part of the merged anytype runner
    "anytype-daemon": AnytypeDaemonRunner,
    "anytype": AnytypeRunner,
    "blender": BlenderRunner,
    "codegraph": CodegraphRunner,
    "context7": Context7Runner,
    "fetch": FetchRunner,
    "lint": LintRunner,
    "mnemosyne": MnemosyneRunner,
    "9router": NinerouterRunner,
    "ponytail": PonytailRunner,
    "qwen-web": QwenWebRunner,
    "skill": SkillRunner,
    "vision": VisionRunner,
    "workspace": WorkspaceRunner,
}
