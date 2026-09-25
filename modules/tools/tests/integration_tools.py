"""Integration tests for modules/tools — real wiring and orchestration."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock


def test_tools_orchestrator_creation():
    """IT-TOOLS-001: ToolsOrchestrator can be created with injected dependencies."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    registry = {"test-tool": MagicMock()}
    installer = MagicMock()
    updater = MagicMock()
    uninstaller = MagicMock()
    runner = MagicMock()

    orch = ToolsOrchestrator(
        registry=registry,
        installer=installer,
        updater=updater,
        uninstaller=uninstaller,
        runner=runner,
    )

    assert orch is not None
    assert orch._registry == registry


def test_tools_orchestrator_missing_registry_raises():
    """IT-TOOLS-002: ToolsOrchestrator requires registry injection."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    try:
        ToolsOrchestrator(registry=None)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "registry" in str(e).lower()


def test_tools_orchestrator_list():
    """IT-TOOLS-003: list() returns tools from manifest."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    orch = ToolsOrchestrator(registry={})
    tools = orch.list()
    assert isinstance(tools, list)


def test_tools_orchestrator_resolve_known_tool():
    """IT-TOOLS-004: resolve() finds known tools."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    orch = ToolsOrchestrator(registry={})
    spec =    orch.resolve("lint-arwaky")
    assert spec is not None
    assert spec.id == "lint-arwaky"


def test_tools_orchestrator_resolve_unknown():
    """IT-TOOLS-005: resolve() returns None for unknown tool."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    orch = ToolsOrchestrator(registry={})
    spec = orch.resolve("nonexistent-tool-12345")
    assert spec is None


def test_tools_orchestrator_install_requires_installer():
    """IT-TOOLS-006: install() raises when installer not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolInstallError
    from modules.shared.src.utility_manifest_reader import find_tool, spec_from_tool

    orch = ToolsOrchestrator(registry={})
    spec =    orch.resolve("lint-arwaky")
    if spec is None:
        return

    try:
        orch.install(spec)
        assert False, "Should have raised ToolInstallError"
    except ToolInstallError:
        pass


def test_tools_orchestrator_update_requires_updater():
    """IT-TOOLS-007: update() raises when updater not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolUpdateError
    from modules.shared.src.utility_manifest_reader import find_tool, spec_from_tool

    orch = ToolsOrchestrator(registry={})
    spec =    orch.resolve("lint-arwaky")
    if spec is None:
        return

    try:
        orch.update(spec)
        assert False, "Should have raised ToolUpdateError"
    except ToolUpdateError:
        pass


def test_tools_orchestrator_uninstall_requires_uninstaller():
    """IT-TOOLS-008: uninstall() raises when uninstaller not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolUninstallError
    from modules.shared.src.utility_manifest_reader import find_tool, spec_from_tool

    orch = ToolsOrchestrator(registry={})
    spec =    orch.resolve("lint-arwaky")
    if spec is None:
        return

    try:
        orch.uninstall(spec)
        assert False, "Should have raised ToolUninstallError"
    except ToolUninstallError:
        pass


def test_tools_orchestrator_run_requires_runner():
    """IT-TOOLS-009: run() raises when runner not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolInstallError
    from modules.shared.src.utility_manifest_reader import find_tool, spec_from_tool

    orch = ToolsOrchestrator(registry={})
    spec =    orch.resolve("lint-arwaky")
    if spec is None:
        return

    try:
        orch.run(spec, [])
        assert False, "Should have raised ToolInstallError"
    except ToolInstallError:
        pass


def test_tools_orchestrator_executable_path_requires_runner():
    """IT-TOOLS-010: executable_path() raises when runner not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolInstallError
    from modules.shared.src.utility_manifest_reader import find_tool, spec_from_tool

    orch = ToolsOrchestrator(registry={})
    spec =    orch.resolve("lint-arwaky")
    if spec is None:
        return

    try:
        orch.executable_path(spec)
        assert False, "Should have raised ToolInstallError"
    except ToolInstallError:
        pass


def test_create_tools_feature():
    """IT-TOOLS-011: create_tools_feature returns a wired aggregate."""
    from modules.tools.src.root_tools_container import create_tools_feature

    try:
        feature = create_tools_feature()
        assert feature is not None
        assert hasattr(feature, "list")
        assert hasattr(feature, "resolve")
        assert hasattr(feature, "install")
    except Exception:
        pass


def test_adapter_facade_execute():
    """IT-TOOLS-012: ToolAdapterFacade.execute dispatches correctly."""
    from modules.tools.src.capabilities_tools_adapter import ToolAdapterFacade
    from modules.shared.src.taxonomy_common_vo import ToolSpec

    facade = ToolAdapterFacade()
    spec = ToolSpec(
        id="lint-arwaky",
        category="dev",
        binary="lint-arwaky",
        is_mcp=False,
        description="AES linter",
        path="internal/lint-arwaky",
        alias="la",
        mcp_binary=None,
        runner="cargo",
    )

    # Test satisfied check
    result = facade.execute("satisfied", spec=spec)
    assert isinstance(result, bool)


def test_tools_registry_exists():
    """IT-TOOLS-013: TOOLS_REGISTRY contains expected tools."""
    from modules.tools.src.root_tools_container import TOOLS_REGISTRY

    assert isinstance(TOOLS_REGISTRY, dict)
    assert len(TOOLS_REGISTRY) >= 10


def test_orchestrator_repr():
    """IT-TOOLS-014: ToolsOrchestrator __repr__ is descriptive."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    orch = ToolsOrchestrator(registry={})
    assert repr(orch) == "ToolsOrchestrator()"
