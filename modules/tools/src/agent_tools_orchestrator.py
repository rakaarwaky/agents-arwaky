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

    # Block 1: Constructor (capability wiring + adapter registry)
    # Block 2: Manifest-driven spec resolution (shared manifest reader)
    # Block 3: Aggregate verb delegation (install/update/uninstall/run_tool)
    """

    #: tool_id -> unified adapter class (root composition data, injected via registry).
    _ADAPTERS: dict[str, type] = {}

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        registry: dict[str, type] | None = None,
        root: Path | None = None,
        daemons=None,
    ) -> None:
        self._root = root or repo_root()
        self._daemons = daemons
        if registry is None:
            raise ValueError("tools orchestrator requires an injected registry (root composition layer)")
        self._ADAPTERS.update(registry)
        # Capabilities are business-action modules; the agent drives them in
        # verb order and the root layer is what wires them (AES201 rule 8).
        from modules.tools.src.capabilities_tools_installer import InstallerCapability
        from modules.tools.src.capabilities_tools_updater import UpdaterCapability
        from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
        from modules.tools.src.capabilities_tools_runner import RunnerCapability

        self._installer = InstallerCapability(root=self._root, daemons=self._daemons)
        self._updater = UpdaterCapability(root=self._root)
        self._uninstaller = UninstallerCapability(daemons=self._daemons)
        self._runner = RunnerCapability()

    # -- Adapter selection --------------------------------------------------------
    def _adapter_for(self, spec: ToolSpec) -> object:
        cls = self._ADAPTERS.get(spec.id)
        if cls is None:
            registered = sorted(self._ADAPTERS)
            raise ToolInstallError(
                f"no adapter registered for '{spec.id}' (registered: {', '.join(registered)})"
            )
        return cls()

    # -- Block 2: Manifest-driven spec resolution --------------------------------
    def list_tools(self) -> list[Tool]:
        """All registered tools (manifest reader, no I/O here)."""
        return load_tools()

    def resolve_spec(self, query: str) -> ToolSpec | None:
        """Resolve a manifest id / binary / alias into a ToolSpec; None when unknown."""
        tool = find_tool(query)
        if tool is None:
            return None
        return _spec_from_tool(tool)

    # -- Block 3: Aggregate verb delegation --------------------------------------
    def _require(self, obj: object, verb: str) -> object:
        """A verb whose capability is unavailable -> typed error, not a partial dispatch."""
        if obj is None:
            raise ToolInstallError(f"{verb} capability is unavailable (not wired)")
        return obj

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

    def run_tool(self, spec: ToolSpec, args: list[str]) -> int:
        """Discover then execute; return the child's real exit code."""
        self._require(self._runner, "run")
        return self._runner.run(spec, args, self._root)

    def executable_path(self, spec: ToolSpec) -> Path | None:
        """Discover the launch path (read-only) for the CLI surface."""
        return self._runner._discover(spec, self._root)

    # -- Direct capability dispatch (capability surfaces) --------------------------
    def provision(self, spec: ToolSpec, adapter: object, dry_run: bool = False) -> InstallResult:
        """FR-001 passthrough to the installer capability."""
        return self._installer.install(spec, adapter, dry_run=dry_run)

    def find_executable(self, spec: ToolSpec) -> Path | None:
        """FR-007: locate the runnable binary for *spec*, or None when not installed."""
        return self._runner._discover(spec, self._root)

    def execute(self, spec: ToolSpec, executable: Path, args: list[str], root: Path | None = None) -> int:
        """FR-008: run a resolved *executable*; return the child's exit code."""
        return self._runner._execute(spec, executable, args, root or self._root)


__all__ = ["ToolsOrchestrator"]
