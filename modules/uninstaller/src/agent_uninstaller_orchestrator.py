"""Uninstaller orchestrator — dispatches ToolSpec to the per-tool capability.

Each per-tool capability mirrors one original tools/uninstall/uninstall_*.py
script. `anytype` (merged mcp + daemon) is fully covered by
AnytypeDaemonUninstaller, which also uninstalls the mcp half; there is no
uninstaller for `skill` (it has no launchers or XDG artifacts).
"""
from __future__ import annotations

from modules.runner.src.contract_tool_runner_aggregate import IToolAggregate

from modules.uninstaller.src.contract_tool_uninstaller_protocol import IToolUninstaller

from pathlib import Path
from typing import cast

from modules.shared.src.utility_paths import repo_root
from modules.uninstaller.src.contract_tool_uninstaller_protocol import IToolUninstaller
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult


class UninstallerOrchestrator(IToolUninstaller):
    """Route uninstall(spec) to the concrete per-tool uninstaller capability.

    # Block 1: Constructor & per-tool registry
    # Block 2: uninstall dispatch
    """

    # -- Block 1: Constructor ------------------------------------------------------
    def __init__(
        self,
        registry: dict[str, object] | dict[str, type] | None = None,
        root: Path | None = None,
    ) -> None:
        self._root = root or repo_root()
        if registry is None:
            raise ValueError(f"uninstaller orchestrator requires an injected registry (root composition layer)")
        self._capabilities: dict[str, IToolUninstaller] = {}
        for tool_id, entry in registry.items():
            if isinstance(entry, type):
                self._capabilities[tool_id] = entry(self._root)
            else:
                self._capabilities[tool_id] = cast(IToolUninstaller, entry)

    # -- Block 2: uninstall dispatch ------------------------------------------------
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        capability = self._capabilities.get(spec.id)
        if capability is None:
            return UninstallResult(True, spec.id, f"{spec.id} has no uninstaller (nothing to remove)")
        return capability.uninstall(spec)
"""Uninstaller orchestrator — dispatches ToolSpec to the per-tool capability.

Each per-tool capability mirrors one original tools/uninstall/uninstall_*.py
script. `anytype` (merged mcp + daemon) is fully covered by
AnytypeDaemonUninstaller, which also uninstalls the mcp half; there is no
uninstaller for `skill` (it has no launchers or XDG artifacts).
"""

from modules.uninstaller.src.contract_tool_uninstaller_protocol import IToolUninstaller

from pathlib import Path
from typing import cast

from modules.shared.src.utility_paths import repo_root
from modules.uninstaller.src.contract_tool_uninstaller_protocol import IToolUninstaller




__all__ = ['IToolAggregate', 'UninstallerOrchestrator']


class UninstallerVerb(IToolAggregate):
    """Agent-layer verb surface for the uninstaller feature (AES405 aggregate implementor)."""

    def __init__(self, orch: UninstallerOrchestrator) -> None:
        self._orch = orch

    def install(self, spec) -> InstallResult:
        return self._orch.install(spec)

    def update(self, spec) -> UpdateResult:
        return self._orch.update(spec)

    def uninstall(self, spec) -> UninstallResult:
        return self._orch.uninstall(spec)

    def list_tools(self):
        return []

    def run_tool(self, spec, args: list[str]) -> int:
        return 0
