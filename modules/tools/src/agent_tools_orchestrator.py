"""Tools orchestrator — single agent driving the action capability classes.

Resolves the target tool spec from the manifest (typed error on unknown ids
BEFORE any capability runs), selects the unified per-tool adapter keyed on
the manifest `id`, and dispatches every aggregate action to its capability
through the single protocol method `execute(op, spec, query, args)`:

- list           : manifest reader → registered tools
- resolve        : query (id / binary / alias) → spec | None
- install        : execute("install", spec)                 (provision + launcher)
- update         : execute("update", spec)                  (bump + record)
- uninstall      : execute("uninstall", spec, owned paths)  (remove + verify)
- run            : execute("run", spec, args)               (discover + exec)
- executable_path: execute("discover", spec)                (read-only path)

Adding a tool is a manifest entry plus one unified adapter — no
orchestrator edit.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from modules.shared.src.contract_tools_aggregate import IToolsAggregate
from modules.shared.src.contract_tools_protocol import IToolsProtocol
from modules.shared.src.taxonomy_common_error import (
    ToolInstallError,
    ToolUninstallError,
    ToolUpdateError,
)
from modules.shared.src.taxonomy_common_vo import (
    InstallResult,
    Tool,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)
from modules.shared.src.taxonomy_tools_vo import ExitCode, ToolQuery
from modules.shared.src.utility_manifest_reader import find_tool, load_tools
from modules.shared.src.utility_paths_resolver import repo_root


def _spec_from_tool(tool: Tool) -> ToolSpec:
    """Build a ToolSpec from a manifest Tool (mcp_binary populated by the reader)."""
    return ToolSpec(
        id=tool.id,
        category=tool.category,
        binary=tool.binary,
        is_mcp=tool.is_mcp,
        description=tool.description,
        path=tool.path,
        alias=tool.alias,
        mcp_binary=getattr(tool, "mcp_binary", None),
        runner=getattr(tool, "runner", None),
    )


class ToolsOrchestrator(IToolsAggregate):
    """Zero-I/O aggregate over all tool-lifecycle capabilities.

    The single entry point the CLI surface calls. Unknown ids fail at
    target resolution before any action runs; an action whose capability is
    unwired raises a typed error, never a partial dispatch.

    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        registry: dict[str, object] | None = None,
        root: Path | None = None,
        daemons=None,
        installer: IToolsProtocol | None = None,
        updater: IToolsProtocol | None = None,
        uninstaller: IToolsProtocol | None = None,
        runner: IToolsProtocol | None = None,
        adapter_facade: IToolsProtocol | None = None,
    ) -> None:
        self._root = root or repo_root()
        self._daemons = daemons
        if registry is None:
            raise ValueError("tools orchestrator requires an injected registry (root composition layer)")
        # P0-2: instance-level copy — was a class-level dict mutated via
        # .update(registry), which leaked entries across orchestrator instances.
        # The registry is consumed only by `resolve`-style lookups; action
        # calls route through the injected adapter facade (P1-7).
        self._registry: dict[str, object] = dict(registry)
        # P1-7: the adapter facade is the single API pipeline over all 13
        # leaf adapters + shared mechanics. The action capabilities already
        # route through it; the orchestrator keeps it for its uninstall()
        # owned_paths call (read-only, no I/O) via facade.execute("owned_paths").
        self._facade = adapter_facade
        # AES201/AES405: the agent layer must not import capabilities_* — the
        # action capabilities are injected by the root composition layer
        # (root_tools_container.create_tools_feature) typed against the single
        # IToolsProtocol contract (execute(op, spec, query, args)). An unwired
        # action stays None and _require() raises a typed error on use, never
        # a partial dispatch.
        self._installer = installer
        self._updater = updater
        self._uninstaller = uninstaller
        self._runner = runner

    # -- Block 2: Manifest-driven spec resolution + aggregate action delegation -----
    def list(self) -> list[Tool]:
        """All registered tools (manifest reader, no I/O here)."""
        return load_tools()

    def resolve(self, query: ToolQuery) -> ToolSpec | None:
        """Resolve a manifest id / binary / alias into a ToolSpec; None when unknown."""
        tool = find_tool(query)
        if tool is None:
            return None
        return _spec_from_tool(tool)

    def install(self, spec: ToolSpec) -> InstallResult:
        self._require(self._installer, "install")
        if find_tool(spec.id) is None:
            raise ToolInstallError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        # P1-1/P1-7: action calls dispatch through the capability's single
        # protocol method; a missing adapter folds into the result.
        return self._installer.execute("install", spec=spec)

    def update(self, spec: ToolSpec) -> UpdateResult:
        self._require(self._updater, "update")
        if find_tool(spec.id) is None:
            raise ToolUpdateError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        # P1-1: fold a missing adapter into the result, same as install().
        return self._updater.execute("update", spec=spec)

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        self._require(self._uninstaller, "uninstall")
        if find_tool(spec.id) is None:
            raise ToolUninstallError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        # P1-1/P1-7: owned_paths routed through the injected adapter facade's
        # execute("owned_paths"); the capability tears down exactly that set.
        if self._facade is None:
            raise ToolUninstallError("adapter facade is unavailable (not wired)")
        owned = self._facade.execute("owned_paths", spec=spec) or []
        return self._uninstaller.execute(
            "uninstall", spec=spec, args=[str(p) for p in owned]
        )

    def run(self, spec: ToolSpec, args: list[str]) -> ExitCode:
        """Discover then execute; return the child's real exit code."""
        self._require(self._runner, "run")
        return self._runner.execute("run", spec=spec, args=args)

    def executable_path(self, spec: ToolSpec) -> Path | None:
        """Discover the launch path (read-only) for the CLI surface.

        Still used by root_cli_entry.py's legacy executable_path() helper
        (P1-6 kept this method; only find_executable/execute were dead).
        """
        self._require(self._runner, "run")
        return self._runner.execute("discover", spec=spec)

    # -- Block 3: Private helpers ---------------------------------------------------
    # P1-2: action-typed error — was always ToolInstallError for every action.
    _ACTION_ERRORS: ClassVar[dict[str, type[Exception]]] = {
        "install": ToolInstallError,
        "update": ToolUpdateError,
        "uninstall": ToolUninstallError,
        "run": ToolInstallError,  # no ToolRunError in taxonomy_common_error today
    }

    def _require(self, obj: object, action: str) -> object:
        """An action whose capability is unavailable -> typed error, not a partial dispatch."""
        if obj is None:
            raise self._ACTION_ERRORS[action](f"{action} capability is unavailable (not wired)")
        return obj


__all__ = ["ToolsOrchestrator"]
