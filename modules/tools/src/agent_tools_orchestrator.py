"""Tools agent orchestrator — single-execute aggregate over the tool capabilities.

Resolves the target tool spec from the manifest (typed error on unknown ids
BEFORE any capability runs), then routes each ``ToolRequest.op`` to the rich
protocol method that owns it:

- list           : manifest reader → every registered tool
- resolve        : query (id / binary / alias) → spec | None
- install        : IToolsInstallerProtocol.install(spec)    (provision + launcher)
- update         : IToolsUpdaterProtocol.update(spec)       (bump + record)
- uninstall      : IToolsUninstallerProtocol.uninstall(spec, owned)  (remove + verify)
- run            : IToolsRunnerProtocol.run(spec, args)     (discover + exec)
- executable_path: IToolsRunnerProtocol.discover(spec)      (read-only path)

Adding a tool is a manifest entry plus one unified adapter — no
orchestrator edit.
"""
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from modules.shared.src.contract_tools_aggregate import IToolsAggregate
from modules.shared.src.contract_tools_protocol import (
    IToolsInstallerProtocol,
    IToolsRunnerProtocol,
    IToolsUninstallerProtocol,
    IToolsUpdaterProtocol,
)
from modules.shared.src.taxonomy_common_error import (
    ToolInstallError,
    ToolUninstallError,
    ToolUpdateError,
)
from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_vo import (
    ExitCode,
    ToolExecutable,
    ToolQuery,
    ToolRequest,
    ToolResponse,
    ToolsOp,
)
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
        installer: IToolsInstallerProtocol | None = None,
        updater: IToolsUpdaterProtocol | None = None,
        uninstaller: IToolsUninstallerProtocol | None = None,
        runner: IToolsRunnerProtocol | None = None,
    ) -> None:
        self._root = root or repo_root()
        self._daemons = daemons
        if registry is None:
            raise ValueError("tools orchestrator requires an injected registry (root composition layer)")
        # Instance-level copy of the injected registry: shared across
        # orchestrator instances without leaking entries. The registry feeds
        # owned_paths lookups in uninstall(); action calls route through the
        # injected capabilities (dependency inversion via the protocol classes).
        self._registry: dict[str, object] = dict(registry)
        # AES201/AES405: the agent layer must not import capabilities_* — the
        # action capabilities are injected by the root composition layer
        # (root_tools_container.create_tools_feature), each typed against the
        # rich protocol class that owns its operations. An unwired action stays
        # None and _require() raises a typed error on use, never a partial
        # dispatch.
        self._installer = installer
        self._updater = updater
        self._uninstaller = uninstaller
        self._runner = runner

    # ─── Block 2: Aggregate Method Implementation ──────────
    def execute(self, request: ToolRequest) -> ToolResponse:
        """Route *request* to the capability that owns the op; return the response."""
        op = ToolsOp(str(request.op))
        if op == "list":
            return ToolResponse(tools=tuple(load_tools()))
        if op == "resolve":
            tool = find_tool(ToolQuery(str(request.query)))
            return ToolResponse(spec=spec_from_tool(tool) if tool is not None else None)
        if op == "install":
            return ToolResponse(install=self._install(request.spec))
        if op == "update":
            return ToolResponse(update=self._update(request.spec))
        if op == "uninstall":
            return ToolResponse(uninstall=self._uninstall(request.spec))
        if op == "run":
            return ToolResponse(run=self._run(request.spec, request.args))
        if op == "executable_path":
            self._require(self._runner, "run")
            if request.spec is None:
                return ToolResponse()
            found = self._runner.discover(request.spec)
            return ToolResponse(executable=ToolExecutable(found) if found is not None else None)
        raise ValueError(f"Unknown tools op: {op}")

    # ─── Block 3: Dunder Methods, Factories & Helpers ─────
    # Action-typed error — each verb raises its own domain error.
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

    def _known(self, spec: ToolSpec) -> bool:
        """True when *spec*'s id resolves against the manifest."""
        return find_tool(spec.id) is not None

    def _install(self, spec: ToolSpec | None):
        """Provision + register launchers for *spec*."""
        self._require(self._installer, "install")
        if spec is None or not self._known(spec):
            raise ToolInstallError(f"unknown tool id or alias '{spec}' (not in manifest)")
        return self._installer.install(spec)

    def _update(self, spec: ToolSpec | None):
        """Bump *spec* to its manifest pin and record the transition."""
        self._require(self._updater, "update")
        if spec is None or not self._known(spec):
            raise ToolUpdateError(f"unknown tool id or alias '{spec}' (not in manifest)")
        return self._updater.update(spec)

    def _uninstall(self, spec: ToolSpec | None):
        """Remove *spec*'s owned paths and verify no residuals remain."""
        self._require(self._uninstaller, "uninstall")
        if spec is None or not self._known(spec):
            raise ToolUninstallError(f"unknown tool id or alias '{spec}' (not in manifest)")
        # owned_paths resolved from the injected registry; the capability
        # tears down exactly that set.
        unit = self._registry.get(spec.id)
        owned_fn = getattr(unit, "owned_paths", None)
        owned: list[Path] = list(owned_fn(spec, self._root) or []) if callable(owned_fn) else []
        return self._uninstaller.uninstall(spec, owned)

    def _run(self, spec: ToolSpec | None, args) -> ExitCode:
        """Discover then execute *spec*; return the child's real exit code."""
        self._require(self._runner, "run")
        if spec is None:
            raise ToolInstallError("run op requires a resolved spec target")
        return self._runner.run(spec, list(args))

    def __repr__(self) -> str:
        return "ToolsOrchestrator()"


__all__ = ["ToolsOrchestrator", "ToolRequest", "ToolResponse"]

# Layer-symbol registry (runtime reference for harness/loader introspection).
_layer_symbols = {
    "ToolsOrchestrator": ToolsOrchestrator,
    "ToolRequest": ToolRequest,
    "ToolResponse": ToolResponse,
}
