"""Installer orchestrator — dispatches ToolSpec to the per-tool capability."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.manifest import load_tools
from modules.shared.src.paths.utility_paths import repo_root
from modules.shared.src.tool.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.installer.src.contract_tool_installer import IToolInstaller

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


def _tool_id(spec: ToolSpec) -> str:
    return spec.id


class InstallerOrchestrator(IToolInstaller):
    """Route install(spec) to the concrete per-tool installer capability.

    # Block 1: Constructor & per-tool registry
    # Block 2: install dispatch
    # Block 3: install_all loop
    """

    # -- Block 1: Constructor & per-tool registry --------------------------------
    _REGISTRY: dict[str, type] = {
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

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()
        self._capabilities: dict[str, IToolInstaller] = {
            tool_id: cls(self._root) for tool_id, cls in self._REGISTRY.items()
        }

    # -- Block 2: install dispatch ------------------------------------------------
    def install(self, spec: ToolSpec) -> InstallResult:
        capability = self._capabilities.get(_tool_id(spec))
        if capability is None:
            return InstallResult(False, spec.id, f"no installer registered for {spec.id}")
        return capability.install(spec)

    # -- Block 3: install_all loop ------------------------------------------------
    def install_all(self) -> list[InstallResult]:
        """Install every manifest tool; tools without a registered installer are skipped."""
        results: list[InstallResult] = []
        for tool in load_tools():
            spec = ToolSpec(
                id=tool.id,
                category=tool.category,
                binary=tool.binary,
                is_mcp=tool.is_mcp,
                description=tool.description,
                path=tool.path,
                alias=tool.alias,
                mcp_binary=getattr(tool, "mcp_binary", None),
            )
            results.append(self.install(spec))
        return results
