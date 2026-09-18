"""Installer orchestrator — dispatches ToolSpec to the per-tool capability."""
from __future__ import annotations

from modules.runner.src.contract_tool_runner_aggregate import IToolAggregate
from modules.installer.src.contract_tool_installer_protocol import IToolInstaller

from pathlib import Path
from typing import cast

from modules.shared.src.utility_manifest_reader import load_tools
from modules.shared.src.utility_paths import repo_root
from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec, UninstallResult, UpdateResult


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
        registry: dict[str, object] | dict[str, type] | None = None,
        root: Path | None = None,
    ) -> None:
        self._root = root or repo_root()
        if registry is None:
            raise ValueError(f"installer orchestrator requires an injected registry (root composition layer)")
        # registry may hold either pre-instantiated capabilities (dict[str, IToolInstaller])
        # or classes to instantiate locally (dict[str, type]).
        self._capabilities: dict[str, IToolInstaller] = {}
        for tool_id, entry in registry.items():
            if isinstance(entry, type):
                self._capabilities[tool_id] = entry(self._root)
            else:
                self._capabilities[tool_id] = cast(IToolInstaller, entry)

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

__all__ = ["IToolAggregate", "InstallerOrchestrator"]


class InstallerVerb(IToolAggregate):
    """Agent-layer verb surface for the installer feature (AES405 aggregate implementor).

    Delegates to the orchestrator where the verb exists (install); update/uninstall
    are no-ops here because the installer feature owns only the install lifecycle.
    """

    def __init__(self, orch: InstallerOrchestrator) -> None:
        self._orch = orch

    def install(self, spec: ToolSpec) -> InstallResult:
        return self._orch.install(spec)

    def update(self, spec: ToolSpec) -> UpdateResult:
        return UpdateResult(success=False, tool_id=spec.id, message="not an updater feature")

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        return UninstallResult(success=False, tool_id=spec.id, message="not an uninstaller feature")

    def list_tools(self):
        return []

    def run_tool(self, spec: ToolSpec, args: list[str]) -> int:
        return 0
