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
from modules.shared.src.utility_manifest_reader import (
    find_tool,
    load_tools,
    spec_from_tool,
)
from modules.shared.src.utility_paths_resolver import repo_root


# ─── Block 1: Class Definition & Constructor ──────────────
class ToolsOrchestrator(IToolsAggregate):
    """Zero-I/O aggregate over all tool-lifecycle capabilities.

    The single entry point the CLI surface calls. Unknown ids fail at
    target resolution before any action runs; an action whose capability is
    unwired raises a typed error, never a partial dispatch.
    """

    def __init__(
        self,
        registry: dict[str, object] | None = None,
        root: Path | None = None,
        daemons=None,
        installer: IToolsProtocol | None = None,
        updater: IToolsProtocol | None = None,
        uninstaller: IToolsProtocol | None = None,
        runner: IToolsProtocol | None = None,
    ) -> None:
        self._root = root or repo_root()
        self._daemons = daemons
        if registry is None:
            raise ValueError("tools orchestrator requires an injected registry (root composition layer)")
        # P0-2: instance-level copy — was a class-level dict mutated via
        # .update(registry), which leaked entries across orchestrator instances.
        # The registry is consumed by owned_paths lookups in uninstall() and
        # by resolver-style queries; action calls route through the injected
        # capabilities (dependency inversion via IToolsProtocol).
        self._registry: dict[str, object] = dict(registry)
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

    # ─── Block 2: Aggregate Method Implementation ──────────
    def list(self) -> list[Tool]:
        """All registered tools (manifest reader, no I/O here)."""
        return load_tools()

    def resolve(self, query: ToolQuery) -> ToolSpec | None:
        """Resolve a manifest id / binary / alias into a ToolSpec; None when unknown."""
        tool = find_tool(query)
        if tool is None:
            return None
        return spec_from_tool(tool)

    def install(self, spec: ToolSpec) -> InstallResult:
        """Install the tool (provision + launcher registration) via the installer capability."""
        self._require(self._installer, "install")
        if find_tool(spec.id) is None:
            raise ToolInstallError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        # P1-1/P1-7: action calls dispatch through the capability's single
        # protocol method; a missing adapter folds into the result.
        return self._installer.execute("install", spec=spec)

    def update(self, spec: ToolSpec) -> UpdateResult:
        """Update the tool to its manifest pin and record the transition."""
        self._require(self._updater, "update")
        if find_tool(spec.id) is None:
            raise ToolUpdateError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        # P1-1: fold a missing adapter into the result, same as install().
        return self._updater.execute("update", spec=spec)

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        """Uninstall the tool (remove owned paths + verify no residuals)."""
        self._require(self._uninstaller, "uninstall")
        if find_tool(spec.id) is None:
            raise ToolUninstallError(f"unknown tool id or alias '{spec.id}' (not in manifest)")
        # P1-1: owned_paths resolved directly from the injected registry;
        # the capability tears down exactly that set.
        unit = self._registry.get(spec.id)
        owned_fn = getattr(unit, "owned_paths", None)
        owned: list[Path] = list(owned_fn(spec, self._root) or []) if callable(owned_fn) else []
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

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
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

    def __repr__(self) -> str:
        return "ToolsOrchestrator()"


__all__ = ["ToolsOrchestrator"]
