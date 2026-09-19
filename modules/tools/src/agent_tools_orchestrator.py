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

from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS
from modules.shared.src.taxonomy_core_error import (
    ToolInstallError,
    ToolUninstallError,
    ToolUpdateError,
)
from modules.shared.src.taxonomy_manifest_vo import Tool
from modules.shared.src.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)
from modules.shared.src.utility_manifest_reader import find_tool, load_tools
from modules.shared.src.utility_paths import repo_root
from modules.tools.src.contract_tools_aggregate import IToolsAggregate
from modules.tools.src.contract_tools_protocol import (
    IToolInstaller,
    IToolRunner,
    IToolUninstaller,
    IToolUpdater,
)
from modules.tools.src.taxonomy_tools_vo import ExitCode, ToolQuery


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
        runner=TOOL_RUNNERS.get(tool.id, ""),
    )


class ToolsOrchestrator(IToolsAggregate):
    """Zero-I/O aggregate over all tool-lifecycle capabilities.

    The single entry point the CLI surface calls. Unknown ids fail at
    target resolution before any verb runs; a verb whose capability is
    unwired raises a typed error, never a partial dispatch.

    """

    #: tool_id -> adapter module (root composition data, injected via registry).
    #: Each value is a stateless leaf module (AES404) of bare verb functions.
    #: Instance-level copy: constructing one orchestrator never leaks entries
    #: into another (no shared class-state mutation).
    _ADAPTERS: dict[str, object] = {}

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
    ) -> None:
        self._root = root or repo_root()
        self._daemons = daemons
        if registry is None:
            raise ValueError("tools orchestrator requires an injected registry (root composition layer)")
        self._ADAPTERS.update(registry)
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
        try:
            adapter = self._adapter_for(spec)
        except ToolInstallError as e:
            return InstallResult(False, spec.id, str(e))

        return self._installer.install(spec, adapter, dry_run=False)

    def update(self, spec: ToolSpec) -> UpdateResult:
        self._require(self._updater, "update")
        if find_tool(spec.id) is None:
            raise ToolUpdateError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        adapter = self._adapter_for(spec)
        return self._updater.update(spec, adapter, dry_run=False)

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        self._require(self._uninstaller, "uninstall")
        if find_tool(spec.id) is None:
            raise ToolUninstallError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        adapter = self._adapter_for(spec)
        owned = adapter.owned_paths(spec, self._root)
        return self._uninstaller.uninstall(spec, owned, dry_run=False)

    def run_tool(self, spec: ToolSpec, args: list[str]) -> ExitCode:
        """Discover then execute; return the child's real exit code."""
        self._require(self._runner, "run")
        return self._runner.run(spec, args, self._root)

    def executable_path(self, spec: ToolSpec) -> Path | None:
        """Discover the launch path (read-only) for the CLI surface."""
        self._require(self._runner, "run")
        return self._runner.discover(spec, self._root)

    # -- Block 3: Private helpers ---------------------------------------------------
    def _require(self, obj: object, verb: str) -> object:
        """A verb whose capability is unavailable -> typed error, not a partial dispatch."""
        if obj is None:
            raise ToolInstallError(f"{verb} capability is unavailable (not wired)")
        return obj

    def _adapter_for(self, spec: ToolSpec) -> object:
        """Return the unified per-tool adapter unit for *spec*.

        Registry values are leaf modules (AES404, module-level verb
        functions). For ids carrying verb overrides (shared-module ids
        like `anytype-daemon`), the root layer pre-builds a SimpleNamespace
        pointing at the module's ``daemon_*`` functions so the capability
        sees a uniform ``satisfied``/``install``/``update``/``owned_paths``
        surface.
        """
        unit = self._ADAPTERS.get(spec.id)
        if unit is None:
            registered = sorted(self._ADAPTERS)
            raise ToolInstallError(
                f"no adapter registered for '{spec.id}' (registered: {', '.join(registered)})"
            )
        return unit

    # -- Direct capability dispatch (capability surfaces) --------------------------
    def provision(self, spec: ToolSpec, adapter: object, dry_run: bool = False) -> InstallResult:
        """FR-001 passthrough to the installer capability."""
        return self._installer.install(spec, adapter, dry_run=dry_run)

    def find_executable(self, spec: ToolSpec) -> Path | None:
        """FR-007: locate the runnable binary for *spec*, or None when not installed."""
        self._require(self._runner, "run")
        return self._runner.discover(spec, self._root)

    def execute(self, spec: ToolSpec, executable: Path, args: list[str], root: Path | None = None) -> int:
        """FR-008: run a resolved *executable*; return the child's exit code."""
        self._require(self._runner, "run")
        return self._runner.execute(spec, executable, args, root or self._root)


__all__ = ["ToolsOrchestrator"]
