"""Tools orchestrator — single agent driving the 4 verb capability classes.

Resolves the target tool spec from the manifest (typed error on unknown ids
BEFORE any capability runs), selects the unified per-tool adapter keyed on
the manifest `id`, and drives the 4 verb classes (each a single public
method; sub-steps are internal to the verb):

- install   : installer.install(spec, adapter)                      (provision + register launcher)
- update    : updater.update(spec, adapter)                         (bump + record transition)
- uninstall : uninstaller.uninstall(spec, owned_paths)              (remove + verify residuals)
- run_tool  : runner.run(spec, args, root)                          (discover + execute)

Adding a tool is a manifest entry plus one unified adapter — no
orchestrator edit.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from modules.shared.src.contract_tools_aggregate import IToolsAggregate
from modules.shared.src.contract_tools_protocol import (
    IToolAdapterFacade,
    IToolInstaller,
    IToolRunner,
    IToolUninstaller,
    IToolUpdater,
)
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
    target resolution before any verb runs; a verb whose capability is
    unwired raises a typed error, never a partial dispatch.

    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        registry: dict[str, object] | None = None,
        root: Path | None = None,
        daemons=None,
        installer: IToolInstaller | None = None,
        updater: IToolUpdater | None = None,
        uninstaller: IToolUninstaller | None = None,
        runner: IToolRunner | None = None,
        adapter_facade: IToolAdapterFacade | None = None,
    ) -> None:
        self._root = root or repo_root()
        self._daemons = daemons
        if registry is None:
            raise ValueError("tools orchestrator requires an injected registry (root composition layer)")
        # P0-2: instance-level copy — was a class-level dict mutated via
        # .update(registry), which leaked entries across orchestrator instances.
        # The registry is consumed only by `resolve`-style lookups; verb
        # calls route through the injected adapter facade (P1-7).
        self._registry: dict[str, object] = dict(registry)
        # P1-7: the adapter facade is the single API pipeline over all 13
        # leaf adapters + shared mechanics. The verb capabilities already
        # route through it; the orchestrator keeps it for its uninstall()
        # owned_paths call (read-only, no I/O).
        self._facade = adapter_facade
        # AES201/AES405: the agent layer must not import capabilities_* — the
        # four verb capabilities are injected by the root composition layer
        # (root_tools_container.create_tools_feature) typed against their
        # contract protocols (IToolInstaller/IToolUpdater/IToolUninstaller/
        # IToolRunner). An unwired verb stays None and _require() raises a
        # typed error on use, never a partial dispatch.
        self._installer = installer
        self._updater = updater
        self._uninstaller = uninstaller
        self._runner = runner

    # -- Block 2: Manifest-driven spec resolution + aggregate verb delegation -----
    def list_tools(self) -> list[Tool]:
        """All registered tools (manifest reader, no I/O here)."""
        return load_tools()

    def resolve_spec(self, query: ToolQuery) -> ToolSpec | None:
        """Resolve a manifest id / binary / alias into a ToolSpec; None when unknown."""
        tool = find_tool(query)
        if tool is None:
            return None
        return _spec_from_tool(tool)

    def install(self, spec: ToolSpec) -> InstallResult:
        self._require(self._installer, "install")
        if find_tool(spec.id) is None:
            raise ToolInstallError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        # P1-1/P1-7: verb calls route through the injected adapter facade
        # (single API pipeline); a missing adapter folds into the result.
        return self._installer.install(spec, None, dry_run=False)

    def update(self, spec: ToolSpec) -> UpdateResult:
        self._require(self._updater, "update")
        if find_tool(spec.id) is None:
            raise ToolUpdateError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        # P1-1: fold a missing adapter into the result, same as install().
        return self._updater.update(spec, None, dry_run=False)

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        self._require(self._uninstaller, "uninstall")
        if find_tool(spec.id) is None:
            raise ToolUninstallError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        # P1-1/P1-7: owned_paths routed through the injected adapter facade.
        if self._facade is None:
            raise ToolUninstallError("adapter facade is unavailable (not wired)")
        owned = self._facade.owned_paths(spec, self._root)
        return self._uninstaller.uninstall(spec, owned, dry_run=False)

    def run_tool(self, spec: ToolSpec, args: list[str]) -> ExitCode:
        """Discover then execute; return the child's real exit code."""
        self._require(self._runner, "run")
        return self._runner.run(spec, args, self._root)

    def executable_path(self, spec: ToolSpec) -> Path | None:
        """Discover the launch path (read-only) for the CLI surface.

        Still used by root_cli_entry.py's legacy executable_path() helper
        (P1-6 kept this method; only find_executable/execute were dead).
        """
        self._require(self._runner, "run")
        return self._runner.discover(spec, self._root)

    # -- Block 3: Private helpers ---------------------------------------------------
    # P1-2: verb-typed error — was always ToolInstallError for every verb.
    _VERB_ERRORS: ClassVar[dict[str, type[Exception]]] = {
        "install": ToolInstallError,
        "update": ToolUpdateError,
        "uninstall": ToolUninstallError,
        "run": ToolInstallError,  # no ToolRunError in taxonomy_common_error today
    }

    def _require(self, obj: object, verb: str) -> object:
        """A verb whose capability is unavailable -> typed error, not a partial dispatch."""
        if obj is None:
            raise self._VERB_ERRORS[verb](f"{verb} capability is unavailable (not wired)")
        return obj


__all__ = ["ToolsOrchestrator"]
