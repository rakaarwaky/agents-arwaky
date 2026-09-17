"""Tool agent orchestrator — coordinates the 4 tool capabilities."""
from __future__ import annotations

from modules.shared.src.common.taxonomy_core_constant import TOOL_RUNNERS
from modules.shared.src.manifest.capabilities_manifest_reader import find_tool, load_tools
from modules.shared.src.manifest.taxonomy_manifest_vo import Tool
from modules.shared.src.tool.contract_tool_aggregate import IToolAggregate
from modules.shared.src.tool.contract_tool_protocol import (
    IToolExecutor,
    IToolInstaller,
    IToolUninstaller,
    IToolUpdater,
)
from modules.shared.src.tool.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)
from modules.tool.src.capabilities_tool_install import ToolInstaller


class ToolOrchestrator(IToolAggregate):
    """Zero-I/O orchestrator over the tool capabilities.

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
