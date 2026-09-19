"""Installer orchestrator — single agent driving the two business capabilities.

Resolves the target tool set from the manifest, selects the per-tool adapter
keyed on the manifest `id`, and drives provisioner then launcher in order.
Adding a tool is a manifest entry plus one new per-tool adapter — no
orchestrator edit.
"""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.taxonomy_core_constant import TOOL_RUNNERS
from modules.shared.src.taxonomy_core_error import ToolInstallError
from modules.shared.src.taxonomy_tool_vo import InstallResult, ToolSpec
from modules.shared.src.taxonomy_manifest_vo import Tool
from modules.shared.src.utility_manifest_reader import load_tools
from modules.shared.src.utility_paths import repo_root
from modules.installer.src.contract_tool_installer_aggregate import IInstallerAggregate
from modules.installer.src.contract_tool_installer_protocol import (
    IToolAdapter,
    IToolInstaller,
)


class InstallerOrchestrator(IToolInstaller, IInstallerAggregate):
    """Drive FR-001 (provisioner) then FR-002 (launcher) for one or all tools."""

    #: tool_id -> adapter class (root composition data, injected via registry).
    _ADAPTERS: dict[str, type] = {}

    # -- Block 1: Constructor (injected registry + capabilities) -------------------
    def __init__(
        self,
        registry: dict[str, type] | None = None,
        root: Path | None = None,
        daemons=None,
    ) -> None:
        self._root = root or repo_root()
        self._daemons = daemons
        if registry is None:
            raise ValueError("installer orchestrator requires an injected registry (root composition layer)")
        self._ADAPTERS.update(registry)
        # Capabilities are business-action modules; root wires them (AES201 rule 8).
        from modules.installer.src.capabilities_installer_provisioner import ProvisionerCapability
        from modules.installer.src.capabilities_installer_launcher import LauncherRegistrarCapability
        self._provisioner = ProvisionerCapability(root=self._root, daemons=self._daemons)
        self._launcher = LauncherRegistrarCapability(root=self._root)

    # -- Block 2: Target resolution (agent-layer concern) --------------------------
    def _spec_for(self, tool: Tool) -> ToolSpec:
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

    def _adapter_for(self, spec: ToolSpec) -> IToolAdapter:
        cls = self._ADAPTERS.get(spec.id)
        if cls is None:
            registered = sorted(self._ADAPTERS)
            raise ToolInstallError(
                f"no adapter registered for '{spec.id}' (registered: {', '.join(registered)})"
            )
        return cls()

    # -- Block 3: install dispatch (IToolInstaller) --------------------------------
    def install(self, spec: ToolSpec) -> InstallResult:
        """Provision then register *spec*; a manifest tool with no registered
        adapter fails with a typed message before any capability runs."""
        try:
            adapter = self._adapter_for(spec)
        except ToolInstallError as e:
            return InstallResult(False, spec.id, str(e))

        result = self._provisioner.provision(spec, adapter)
        if not result.success:
            return result
        return self._launcher.register_launcher(spec, result)

    # -- Direct capability dispatch (IToolProvisioner surface) ---------------------
    def provision(self, spec: ToolSpec, adapter: IToolAdapter, dry_run: bool = False) -> InstallResult:
        """FR-001 passthrough to the provisioner capability."""
        return self._provisioner.provision(spec, adapter, dry_run=dry_run)

    def register_launcher(self, spec: ToolSpec, install_result: InstallResult) -> InstallResult:
        """FR-002 passthrough to the launcher registrar capability."""
        return self._launcher.register_launcher(spec, install_result)

    # -- Block 4: install_all loop --------------------------------------------------
    def install_all(self) -> list[InstallResult]:
        """Install every manifest tool; tools without a registered adapter fail with a typed message."""
        return [self.install(self._spec_for(tool)) for tool in load_tools()]


class InstallerVerb(IToolInstaller):
    """Agent-layer verb surface for the installer feature (AES405 aggregate implementor).

    Delegates to the orchestrator where the verb exists (install); update/uninstall
    are no-ops because the installer feature owns only the install lifecycle.
    """

    def __init__(self, orch: InstallerOrchestrator) -> None:
        self._orch = orch

    def provision(self, spec: ToolSpec, adapter: IToolAdapter, dry_run: bool = False) -> InstallResult:
        return InstallResult(False, spec.id, "verb surface does not provision; use InstallerOrchestrator")

    def register_launcher(self, spec: ToolSpec, install_result: InstallResult) -> InstallResult:
        return install_result



__all__ = ["InstallerOrchestrator", "InstallerVerb"]
