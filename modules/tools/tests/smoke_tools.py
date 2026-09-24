"""Smoke tests for modules/tools — fast boot and import checks."""
from __future__ import annotations

import time


def test_import_tools_module():
    """SM-TOOLS-001: modules.tools can be imported."""
    import modules.tools
    assert modules.tools is not None


def test_import_tools_src():
    """SM-TOOLS-002: modules.tools.src can be imported."""
    import modules.tools.src
    assert modules.tools.src is not None


def test_import_capabilities_installer():
    """SM-TOOLS-003: InstallerCapability can be imported."""
    from modules.tools.src.capabilities_tools_installer import InstallerCapability
    assert InstallerCapability is not None


def test_import_capabilities_updater():
    """SM-TOOLS-004: UpdaterCapability can be imported."""
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability
    assert UpdaterCapability is not None


def test_import_capabilities_uninstaller():
    """SM-TOOLS-005: UninstallerCapability can be imported."""
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
    assert UninstallerCapability is not None


def test_import_capabilities_runner():
    """SM-TOOLS-006: RunnerCapability can be imported."""
    from modules.tools.src.capabilities_tools_runner import RunnerCapability
    assert RunnerCapability is not None


def test_import_capabilities_adapter():
    """SM-TOOLS-007: ToolAdapterFacade can be imported."""
    from modules.tools.src.capabilities_tools_adapter import ToolAdapterFacade
    assert ToolAdapterFacade is not None


def test_import_agent_orchestrator():
    """SM-TOOLS-008: ToolsOrchestrator can be imported."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    assert ToolsOrchestrator is not None


def test_import_root_container():
    """SM-TOOLS-009: root_tools_container can be imported."""
    from modules.tools.src.root_tools_container import create_tools_feature, TOOLS_REGISTRY
    assert create_tools_feature is not None
    assert TOOLS_REGISTRY is not None


def test_import_contract_protocols():
    """SM-TOOLS-010: contract protocols can be imported."""
    from modules.shared.src.contract_tools_protocol import IToolsProtocol
    from modules.shared.src.contract_tools_aggregate import IToolsAggregate

    assert IToolsProtocol is not None
    assert IToolsAggregate is not None


def test_import_common_vos():
    """SM-TOOLS-011: common VOs can be imported."""
    from modules.shared.src.taxonomy_common_vo import (
        InstallResult,
        ToolSpec,
        UninstallResult,
        UpdateResult,
    )

    assert InstallResult is not None
    assert ToolSpec is not None
    assert UninstallResult is not None
    assert UpdateResult is not None


def test_import_common_errors():
    """SM-TOOLS-012: domain errors can be imported."""
    from modules.shared.src.taxonomy_common_error import (
        ToolInstallError,
        ToolUpdateError,
        ToolUninstallError,
    )

    assert ToolInstallError is not None
    assert ToolUpdateError is not None
    assert ToolUninstallError is not None


def test_capability_instantiation_quick():
    """SM-TOOLS-013: Capabilities can be instantiated quickly."""
    from modules.tools.src.capabilities_tools_installer import InstallerCapability
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
    from modules.tools.src.capabilities_tools_runner import RunnerCapability

    start = time.time()
    InstallerCapability()
    UpdaterCapability()
    UninstallerCapability()
    RunnerCapability()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Instantiation took {elapsed:.2f}s, expected <1s"


def test_orchestrator_creation_quick():
    """SM-TOOLS-014: ToolsOrchestrator creation completes within 1 second."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    start = time.time()
    orch = ToolsOrchestrator(registry={})
    elapsed = time.time() - start

    assert elapsed < 1.0
    assert orch is not None


def test_manifest_loads_quickly():
    """SM-TOOLS-015: Manifest loading completes within 5 seconds."""
    from modules.shared.src.utility_manifest_reader import load_tools

    start = time.time()
    tools = load_tools()
    elapsed = time.time() - start

    assert elapsed < 5.0, f"Manifest load took {elapsed:.2f}s, expected <5s"
    assert isinstance(tools, list)
    assert len(tools) > 0


def test_tool_registry_accessible():
    """SM-TOOLS-016: Tool registry is accessible."""
    from modules.tools.src.root_tools_container import TOOLS_REGISTRY

    assert isinstance(TOOLS_REGISTRY, dict)
    assert len(TOOLS_REGISTRY) > 0


def test_adapter_facade_creation():
    """SM-TOOLS-017: ToolAdapterFacade can be created."""
    from modules.tools.src.capabilities_tools_adapter import ToolAdapterFacade

    facade = ToolAdapterFacade()
    assert facade is not None
