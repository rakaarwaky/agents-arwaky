"""Installer orchestrator — dispatches ToolSpec to the per-tool capability."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.utility_manifest_reader import load_tools
from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.installer.src.contract_tool_installer import IToolInstaller


def _tool_id(spec: ToolSpec) -> str:
    return spec.id


class InstallerOrchestrator(IToolInstaller):
    """Route install(spec) to the concrete per-tool installer capability.

    # Block 1: Constructor (injected registry from root composition layer)
    # Block 2: install dispatch
    # Block 3: install_all loop
    """

    # -- Block 1: Constructor ------------------------------------------------------
    def __init__(
        self,
        registry: dict[str, type] | None = None,
        root: Path | None = None,
    ) -> None:
        self._root = root or repo_root()
        if registry is None:
            from modules.installer.src.root_tool_installer_registry import (
                INSTALLER_REGISTRY as registry,
            )
        self._capabilities: dict[str, IToolInstaller] = {
            tool_id: cls(self._root) for tool_id, cls in registry.items()
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
