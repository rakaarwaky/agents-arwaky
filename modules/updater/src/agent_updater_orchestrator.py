"""Updater orchestrator — dispatches ToolSpec to the per-tool capability.

Each per-tool capability mirrors one original tools/update/update_*.py
script (12 tools). `anytype` and `anytype-daemon` share the merged
AnytypeUpdater. There is no updater for `skill` (nothing to rebuild).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.contract_tool_protocol import IToolUpdater
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UpdateResult

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


class UpdaterOrchestrator(IToolUpdater):
    """Route update(spec) to the concrete per-tool updater capability.

    # Block 1: Constructor & per-tool registry
    # Block 2: update dispatch
    """

    # -- Block 1: Constructor & per-tool registry --------------------------------
    _REGISTRY: dict[str, type] = {
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

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()
        self._capabilities: dict[str, IToolUpdater] = {
            tool_id: cls(self._root) for tool_id, cls in self._REGISTRY.items()
        }

    # -- Block 2: update dispatch -------------------------------------------------
    def update(self, spec: ToolSpec) -> UpdateResult:
        capability = self._capabilities.get(spec.id)
        if capability is None:
            return UpdateResult(True, spec.id, f"{spec.id} has no updater (nothing to rebuild)")
        return capability.update(spec)
