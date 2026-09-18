"""Uninstaller orchestrator — dispatches ToolSpec to the per-tool capability.

Each per-tool capability mirrors one original tools/uninstall/uninstall_*.py
script. `anytype` (merged mcp + daemon) is fully covered by
AnytypeDaemonUninstaller, which also uninstalls the mcp half; there is no
uninstaller for `skill` (it has no launchers or XDG artifacts).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.paths.utility_paths import repo_root
from modules.uninstaller.src.contract_tool_uninstaller import IToolUninstaller
from modules.shared.src.tool.taxonomy_tool_vo import ToolSpec, UninstallResult

from modules.uninstaller.src.capabilities_anytype_daemon_uninstaller import AnytypeDaemonUninstaller
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


class UninstallerOrchestrator(IToolUninstaller):
    """Route uninstall(spec) to the concrete per-tool uninstaller capability.

    # Block 1: Constructor & per-tool registry
    # Block 2: uninstall dispatch
    """

    # -- Block 1: Constructor & per-tool registry --------------------------------
    _REGISTRY: dict[str, type] = {
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

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()
        self._capabilities: dict[str, IToolUninstaller] = {
            tool_id: cls(self._root) for tool_id, cls in self._REGISTRY.items()
        }

    # -- Block 2: uninstall dispatch ------------------------------------------------
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        capability = self._capabilities.get(spec.id)
        if capability is None:
            return UninstallResult(True, spec.id, f"{spec.id} has no uninstaller (nothing to remove)")
        return capability.uninstall(spec)
