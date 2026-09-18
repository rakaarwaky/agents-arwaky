"""Updater orchestrator — dispatches ToolSpec to the per-tool capability.

Each per-tool capability mirrors one original tools/update/update_*.py
script (12 tools). `anytype` and `anytype-daemon` share the merged
AnytypeUpdater. There is no updater for `skill` (nothing to rebuild).
"""
from __future__ import annotations

from modules.runner.src.contract_tool_runner_aggregate import IToolAggregate

from pathlib import Path
from typing import cast

from modules.shared.src.utility_paths import repo_root
from modules.updater.src.contract_tool_updater_protocol import IToolUpdater
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult


class UpdaterOrchestrator(IToolUpdater):
    """Route update(spec) to the concrete per-tool updater capability.

    # Block 1: Constructor & per-tool registry
    # Block 2: update dispatch
    """

    # -- Block 1: Constructor ------------------------------------------------------
    def __init__(
        self,
        registry: dict[str, object] | dict[str, type] | None = None,
        root: Path | None = None,
    ) -> None:
        self._root = root or repo_root()
        if registry is None:
            raise ValueError(f"updater orchestrator requires an injected registry (root composition layer)")
        self._capabilities: dict[str, IToolUpdater] = {}
        for tool_id, entry in registry.items():
            if isinstance(entry, type):
                self._capabilities[tool_id] = entry(self._root)
            else:
                self._capabilities[tool_id] = cast(IToolUpdater, entry)

    # -- Block 2: update dispatch -------------------------------------------------
    def update(self, spec: ToolSpec) -> UpdateResult:
        capability = self._capabilities.get(spec.id)
        if capability is None:
            return UpdateResult(True, spec.id, f"{spec.id} has no updater (nothing to rebuild)")
        return capability.update(spec)
"""Updater orchestrator — dispatches ToolSpec to the per-tool capability.

Each per-tool capability mirrors one original tools/update/update_*.py
script (12 tools). `anytype` and `anytype-daemon` share the merged
AnytypeUpdater. There is no updater for `skill` (nothing to rebuild).
"""

from modules.updater.src.contract_tool_updater_protocol import IToolUpdater

from pathlib import Path
from typing import cast

from modules.shared.src.utility_paths import repo_root
from modules.updater.src.contract_tool_updater_protocol import IToolUpdater




__all__ = ['IToolAggregate', 'UpdaterOrchestrator']


class UpdaterVerb(IToolAggregate):
    """Agent-layer verb surface for the updater feature (AES405 aggregate implementor)."""

    def __init__(self, orch: UpdaterOrchestrator) -> None:
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
