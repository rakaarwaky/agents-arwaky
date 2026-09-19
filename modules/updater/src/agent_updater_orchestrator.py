"""Updater orchestrator — the single agent verb over the two capabilities.

Resolves the target tool set from the manifest, selects the per-tool adapter
keyed on the manifest `id`, and drives bumper then recorder in order. Adding
a tool is a manifest entry plus one new `utility_<tool>_updater.py` adapter —
no orchestrator edit required.
"""
from __future__ import annotations

from pathlib import Path
from typing import cast

from modules.shared.src.taxonomy_core_error import ToolUpdateError
from modules.shared.src.taxonomy_manifest_vo import Tool
from modules.shared.src.taxonomy_tool_vo import ToolSpec, UpdateResult
from modules.shared.src.utility_manifest_reader import load_tools, find_tool
from modules.shared.src.utility_paths import repo_root
from modules.updater.src.capabilities_updater_bumper import UpdaterBumper
from modules.updater.src.capabilities_updater_recorder import UpdaterRecorder
from modules.updater.src.contract_tool_updater_protocol import (
    IToolUpdater,
    IToolUpdaterAdapter,
)


def _spec_from_tool(tool: Tool) -> ToolSpec:
    from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS
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


def _resolve_spec(query: str) -> ToolSpec:
    """Resolve a manifest id / binary / alias into a ToolSpec; typed error if unknown."""
    tool = find_tool(query)
    if tool is None:
        known = ", ".join(sorted(t.id for t in load_tools()))
        raise ToolUpdateError(
            f"unknown tool id {query!r}; no manifest entry (known ids: {known})"
        )
    return _spec_from_tool(tool)


class UpdaterOrchestrator(IToolUpdater):
    """Drive the update verb: adapter selection by id, bumper, recorder.

    # Block 1: Constructor & adapter registry
    # Block 2: update dispatch
    """

    # Adapter class keyed on manifest id; extended by registering new leaf adapters.
    _ADAPTERS: dict[str, type] = {}

    # -- Block 1: Constructor ------------------------------------------------------
    def __init__(
        self,
        registry: dict[str, object] | None = None,
        root: Path | None = None,
        bumper: UpdaterBumper | None = None,
        recorder: UpdaterRecorder | None = None,
    ) -> None:
        self._root = root or repo_root()
        self._bumper = bumper or UpdaterBumper()
        self._recorder = recorder or UpdaterRecorder()
        if registry is not None:
            self._instances: dict[str, IToolUpdaterAdapter] = {
                tool_id: self._coerce(entry) for tool_id, entry in registry.items()
            }
        else:
            self._instances = {tool_id: cls() for tool_id, cls in self._ADAPTERS.items()}

    @staticmethod
    def _coerce(entry) -> IToolUpdaterAdapter:
        if isinstance(entry, type):
            return entry()
        return cast(IToolUpdaterAdapter, entry)

    # -- Block 2: update dispatch --------------------------------------------------
    def update(self, spec: ToolSpec) -> UpdateResult:
        adapter = self._instances.get(spec.id)
        if adapter is None:
            registered = ", ".join(sorted(self._instances))
            return UpdateResult(
                False, spec.id,
                f"no updater adapter registered for {spec.id!r} "
                f"(registered: {registered})",
            )
        bump_result = self._bumper.bump(spec, adapter, dry_run=False, root=self._root)
        record_result = self._recorder.record(spec, bump_result)
        if bump_result.success and not record_result.success:
            return record_result
        if bump_result.success and record_result.success:
            return UpdateResult(True, spec.id, record_result.message)
        return bump_result


__all__ = ["UpdaterOrchestrator"]
