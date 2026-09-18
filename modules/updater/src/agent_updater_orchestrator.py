"""Updater orchestrator — dispatches ToolSpec to the per-tool capability.

Each per-tool capability mirrors one original tools/update/update_*.py
script (12 tools). `anytype` and `anytype-daemon` share the merged
AnytypeUpdater. There is no updater for `skill` (nothing to rebuild).
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.utility_paths import repo_root
from modules.updater.src.contract_tool_updater import IToolUpdater
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult


class UpdaterOrchestrator(IToolUpdater):
    """Route update(spec) to the concrete per-tool updater capability.

    # Block 1: Constructor & per-tool registry
    # Block 2: update dispatch
    """

    # -- Block 1: Constructor ------------------------------------------------------
    def __init__(
        self,
        registry: dict[str, type] | None = None,
        root: Path | None = None,
    ) -> None:
        self._root = root or repo_root()
        if registry is None:
            from modules.updater.src.root_tool_updater_registry import (
                UPDATER_REGISTRY as registry,
            )
        self._capabilities: dict[str, IToolUpdater] = {
            tool_id: cls(self._root) for tool_id, cls in registry.items()
        }

    # -- Block 2: update dispatch -------------------------------------------------
    def update(self, spec: ToolSpec) -> UpdateResult:
        capability = self._capabilities.get(spec.id)
        if capability is None:
            return UpdateResult(True, spec.id, f"{spec.id} has no updater (nothing to rebuild)")
        return capability.update(spec)
