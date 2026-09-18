"""Runner orchestrator — dispatches ToolSpec to the per-tool runner capability."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS
from modules.shared.src.utility_manifest_reader import find_tool, load_tools
from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_manifest_vo import Tool
from modules.installer.src.contract_tool_installer import IToolInstaller
from modules.runner.src.contract_tool_runner import IToolAggregate, IToolExecutor
from modules.uninstaller.src.contract_tool_uninstaller import IToolUninstaller
from modules.updater.src.contract_tool_updater import IToolUpdater
from modules.shared.src.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)

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


def _tool_id(spec: ToolSpec) -> str:
    return spec.id


class RunnerOrchestrator:
    """Route execution to the concrete per-tool runner capability.

    # Block 1: Constructor & per-tool registry
    # Block 2: IToolExecutor dispatch
    # Block 3: Manifest-driven spec resolution
    """

    # -- Block 1: Constructor & per-tool registry --------------------------------
    _REGISTRY: dict[str, type] = {
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

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or repo_root()
        self._capabilities: dict[str, IToolExecutor] = {
            tool_id: cls(self._root) for tool_id, cls in self._REGISTRY.items()
        }

    # -- Block 2: IToolExecutor dispatch -------------------------------------------
    def find_executable(self, spec: ToolSpec):
        """Locate the runnable binary for *spec*, or None when not installed."""
        capability = self._capabilities.get(_tool_id(spec))
        if capability is None:
            return None
        return capability.find_executable(spec)

    def run(self, spec: ToolSpec, args: list[str]) -> int:
        """Execute *spec* via its per-tool capability; 1 when none registered."""
        capability = self._capabilities.get(_tool_id(spec))
        if capability is None:
            return 1
        return capability.run(spec, args)

    # -- Block 3: Manifest-driven spec resolution -----------------------------------
    def list_tools(self) -> list[Tool]:
        """All registered tools (manifest reader, no I/O here)."""
        return load_tools()

    def resolve_spec(self, query: str) -> ToolSpec | None:
        """Resolve a manifest id/binary/alias into a ToolSpec."""
        tool = find_tool(query)
        if tool is None:
            return None
        return ToolSpec(
            id=tool.id,
            category=tool.category,
            binary=tool.binary,
            is_mcp=tool.is_mcp,
            description=tool.description,
            path=tool.path,
            alias=tool.alias,
            mcp_binary=getattr(tool, "mcp_binary", None),
            runner=TOOL_RUNNERS.get(tool.id, ""),
        )


class ToolOrchestrator(IToolAggregate):
    """Zero-I/O aggregate orchestrator over the 4 tool capabilities.

    # Block 1: Constructor (capability injection)
    # Block 2: Manifest-driven spec resolution
    # Block 3: Aggregate verb delegation
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        executor: IToolExecutor,
        installer: IToolInstaller,
        updater: IToolUpdater,
        uninstaller: IToolUninstaller,
    ) -> None:
        self._executor = executor
        self._installer = installer
        self._updater = updater
        self._uninstaller = uninstaller

    # -- Block 2: Manifest-driven spec resolution --------------------------------
    def list_tools(self) -> list[Tool]:
        """All registered tools (manifest reader, no I/O here)."""
        return load_tools()

    def resolve_spec(self, query: str) -> ToolSpec | None:
        """Resolve a manifest id/binary/alias into a ToolSpec."""
        tool = find_tool(query)
        if tool is None:
            return None
        return ToolSpec(
            id=tool.id,
            category=tool.category,
            binary=tool.binary,
            is_mcp=tool.is_mcp,
            description=tool.description,
            path=tool.path,
            alias=tool.alias,
            mcp_binary=getattr(tool, "mcp_binary", None),
            runner=TOOL_RUNNERS.get(tool.id, ""),
        )

    # -- Block 3: Aggregate verb delegation --------------------------------------
    def install(self, spec: ToolSpec) -> InstallResult:
        return self._installer.install(spec)

    def update(self, spec: ToolSpec) -> UpdateResult:
        return self._updater.update(spec)

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        return self._uninstaller.uninstall(spec)

    def run_tool(self, spec: ToolSpec, args: list[str]) -> int:
        return self._executor.run(spec, args)

    def executable_path(self, spec: ToolSpec):
        return self._executor.find_executable(spec)
