"""Uninstaller orchestrator — dispatches ToolSpec to the per-tool capability.

Each per-tool capability mirrors one original tools/uninstall/uninstall_*.py
script. `anytype` (merged mcp + daemon) is fully covered by
AnytypeDaemonUninstaller, which also uninstalls the mcp half; there is no
uninstaller for `skill` (it has no launchers or XDG artifacts).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.utility_paths import repo_root
from modules.uninstaller.src.contract_tool_uninstaller import IToolUninstaller
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UninstallResult


class UninstallerOrchestrator(IToolUninstaller):
    """Route uninstall(spec) to the concrete per-tool uninstaller capability.

    # Block 1: Constructor & per-tool registry
    # Block 2: uninstall dispatch
    """

    # -- Block 1: Constructor ------------------------------------------------------
    def __init__(
        self,
        registry: dict[str, type] | None = None,
        root: Path | None = None,
    ) -> None:
        self._root = root or repo_root()
        if registry is None:
            from modules.uninstaller.src.root_tool_uninstaller_registry import (
                UNINSTALLER_REGISTRY as registry,
            )
        self._capabilities: dict[str, IToolUninstaller] = {
            tool_id: cls(self._root) for tool_id, cls in registry.items()
        }

    # -- Block 2: uninstall dispatch ------------------------------------------------
    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        capability = self._capabilities.get(spec.id)
        if capability is None:
            return UninstallResult(True, spec.id, f"{spec.id} has no uninstaller (nothing to remove)")
        return capability.uninstall(spec)
