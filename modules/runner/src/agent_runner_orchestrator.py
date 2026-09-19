"""Runner orchestrator — drives the two runner capabilities (FR-001/FR-002)
and exposes the zero-I/O tool-lifecycle aggregate (FR-003).

`RunnerOrchestrator` composes the discoverer + executor capabilities and is
the IToolExecutor the aggregate holds. `ToolOrchestrator` is the single CLI
entry point: it delegates install / update / uninstall to the sibling
lifecycle roots and run to the runner. All side effects live in the
capability it delegates to; the aggregate holds no branching on tool id
or runner family.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS
from modules.shared.src.taxonomy_core_error import ToolInstallError
from modules.shared.src.taxonomy_manifest_vo import Tool
from modules.shared.src.taxonomy_tool_vo import (
    InstallResult,
    ToolSpec,
    UninstallResult,
    UpdateResult,
)
from modules.shared.src.utility_manifest_reader import find_tool, load_tools
from modules.shared.src.utility_paths import repo_root
from modules.runner.src.contract_tool_runner_aggregate import IToolAggregate
from modules.runner.src.contract_tool_runner_protocol import (
    IToolDiscoverer,
    IToolExecutor,
)
from modules.runner.src.capabilities_runner_discoverer import RunnerDiscoverer
from modules.runner.src.capabilities_runner_executor import RunnerExecutor


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


class RunnerOrchestrator(IToolExecutor):
    """Drive discover (FR-001) then execute (FR-002) for a ToolSpec.

    # Block 1: Constructor (capability wiring)
    # Block 2: IToolExecutor dispatch
    # Block 3: Manifest-driven spec resolution
    """

    # -- Block 1: Constructor ------------------------------------------------------
    def __init__(
        self,
        discoverer: IToolDiscoverer | None = None,
        executor: RunnerExecutor | None = None,
        root: Path | None = None,
    ) -> None:
        self._root = root or repo_root()
        self._discoverer = discoverer or RunnerDiscoverer()
        self._executor = executor or RunnerExecutor()

    # -- Block 2: IToolExecutor dispatch --------------------------------------------
    def find_executable(self, spec: ToolSpec) -> Path | None:
        """FR-001: locate the runnable binary for *spec*, or None when not installed."""
        return self._discoverer.discover(spec, self._root)

    def executable_path(self, spec: ToolSpec) -> Path | None:
        """Alias kept for the CLI surface: discover the launch path."""
        return self.find_executable(spec)

    def run(self, spec: ToolSpec, args: list[str]) -> int:
        """Discover then execute; return the child's real exit code."""
        exe = self._discoverer.discover(spec, self._root)
        if exe is None:
            return 1
        return self._executor.execute(spec, exe, args, self._root)

    def execute(self, spec: ToolSpec, executable: Path, args: list[str], root: Path | None = None) -> int:
        """IToolExecutor: run a resolved *executable*; return the child's exit code."""
        return self._executor.execute(spec, executable, args, root or self._root)

    # -- Block 3: Manifest-driven spec resolution ------------------------------------
    def list_tools(self) -> list[Tool]:
        """All registered tools (manifest reader, no I/O here)."""
        return load_tools()

    def resolve_spec(self, query: str) -> ToolSpec | None:
        """Resolve a manifest id/binary/alias into a ToolSpec; None when unknown."""
        tool = find_tool(query)
        if tool is None:
            return None
        return _spec_from_tool(tool)


class ToolOrchestrator(IToolAggregate):
    """Zero-I/O aggregate over the 4 tool-lifecycle capabilities.

    The single entry point the CLI surface calls. Composes the installer /
    updater / uninstaller roots plus this module's runner orchestrator; every
    side effect lives in the delegated capability. Unknown ids fail at
    target resolution before any verb runs.

    # Block 1: Constructor (capability injection)
    # Block 2: Manifest-driven spec resolution (shared manifest reader)
    # Block 3: Aggregate verb delegation (typed error on unknown targets)
    """

    # -- Block 1: Constructor ---------------------------------------------------
    def __init__(
        self,
        executor: IToolExecutor,
        installer: object,
        updater: object,
        uninstaller: object,
    ) -> None:
        self._executor = executor
        self._installer = installer
        self._updater = updater
        self._uninstaller = uninstaller

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
    def _resolve(self, spec: ToolSpec) -> None:
        """Fail unknown ids/aliases before any capability runs (FRD target resolution)."""
        if find_tool(spec.id) is None:
            raise ToolInstallError(
                f"unknown tool id or alias '{spec.id}' (not in manifest)"
            )

    def _require(self, obj: object, verb: str) -> object:
        """A verb whose capability is unavailable -> typed error, not a partial dispatch."""
        if obj is None:
            raise ToolInstallError(f"{verb} capability is unavailable (not wired)")
        return obj

    def install(self, spec: ToolSpec) -> InstallResult:
        self._resolve(spec)
        installer = self._require(self._installer, "install")
        return installer.install(spec)  # type: ignore[attr-defined]

    def update(self, spec: ToolSpec) -> UpdateResult:
        self._resolve(spec)
        updater = self._require(self._updater, "update")
        return updater.update(spec)  # type: ignore[attr-defined]

    def uninstall(self, spec: ToolSpec) -> UninstallResult:
        self._resolve(spec)
        uninstaller = self._require(self._uninstaller, "uninstall")
        return uninstaller.uninstall(spec)  # type: ignore[attr-defined]

    def run_tool(self, spec: ToolSpec, args: list[str]) -> int:
        return self._executor.run(spec, args)

    def executable_path(self, spec: ToolSpec) -> Path | None:
        """Discover the launch path (read-only) for the CLI surface."""
        return self._executor.find_executable(spec)
