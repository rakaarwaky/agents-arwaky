"""Integration tests for modules/tools — real wiring and orchestration."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from modules.shared.src.taxonomy_common_vo import ToolSpec
from modules.shared.src.taxonomy_tools_vo import (
    ToolArgs,
    ToolQuery,
    ToolRequest,
    ToolResponse,
    ToolsOp,
)


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
    """IT-TOOLS-003: execute(list) returns the tool list."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    orch = ToolsOrchestrator(registry={})
    response = orch.execute(ToolRequest(ToolsOp("list")))
    assert response.tools is not None
    assert len(response.tools) >= 10


def test_tools_orchestrator_resolve_known_tool():
    """IT-TOOLS-004: execute(resolve) finds known tools."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    orch = ToolsOrchestrator(registry={})
    response = orch.execute(ToolRequest(ToolsOp("resolve"), query=ToolQuery("lint-arwaky")))
    assert response.spec is not None
    assert response.spec.id == "lint-arwaky"


def test_tools_orchestrator_resolve_unknown():
    """IT-TOOLS-005: execute(resolve) returns None for unknown tool."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    orch = ToolsOrchestrator(registry={})
    response = orch.execute(
        ToolRequest(ToolsOp("resolve"), query=ToolQuery("nonexistent-tool-12345"))
    )
    assert response.spec is None


def test_tools_orchestrator_install_requires_installer():
    """IT-TOOLS-006: install raises when installer not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolInstallError

    orch = ToolsOrchestrator(registry={})
    spec = orch.execute(
        ToolRequest(ToolsOp("resolve"), query=ToolQuery("lint-arwaky"))
    ).spec
    if spec is None:
        raise AssertionError("lint-arwaky must be in manifest")

    try:
        orch.execute(ToolRequest(ToolsOp("install"), spec=spec))
        assert False, "Should have raised ToolInstallError"
    except ToolInstallError:
        pass


def test_tools_orchestrator_update_requires_updater():
    """IT-TOOLS-007: update raises when updater not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolUpdateError

    orch = ToolsOrchestrator(registry={})
    spec = orch.execute(
        ToolRequest(ToolsOp("resolve"), query=ToolQuery("lint-arwaky"))
    ).spec
    if spec is None:
        raise AssertionError("lint-arwaky must be in manifest")

    try:
        orch.execute(ToolRequest(ToolsOp("update"), spec=spec))
        assert False, "Should have raised ToolUpdateError"
    except ToolUpdateError:
        pass


def test_tools_orchestrator_uninstall_requires_uninstaller():
    """IT-TOOLS-008: uninstall raises when uninstaller not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolUninstallError

    orch = ToolsOrchestrator(registry={})
    spec = orch.execute(
        ToolRequest(ToolsOp("resolve"), query=ToolQuery("lint-arwaky"))
    ).spec
    if spec is None:
        raise AssertionError("lint-arwaky must be in manifest")

    try:
        orch.execute(ToolRequest(ToolsOp("uninstall"), spec=spec))
        assert False, "Should have raised ToolUninstallError"
    except ToolUninstallError:
        pass


def test_tools_orchestrator_run_requires_runner():
    """IT-TOOLS-009: run raises when runner not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolInstallError

    orch = ToolsOrchestrator(registry={})
    spec = orch.execute(
        ToolRequest(ToolsOp("resolve"), query=ToolQuery("lint-arwaky"))
    ).spec
    if spec is None:
        raise AssertionError("lint-arwaky must be in manifest")

    try:
        orch.execute(ToolRequest(ToolsOp("run"), spec=spec, args=ToolArgs([])))
        assert False, "Should have raised ToolInstallError"
    except ToolInstallError:
        pass


def test_tools_orchestrator_executable_path_requires_runner():
    """IT-TOOLS-010: executable_path raises when runner not wired."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator
    from modules.shared.src.taxonomy_common_error import ToolInstallError

    orch = ToolsOrchestrator(registry={})
    spec = orch.execute(
        ToolRequest(ToolsOp("resolve"), query=ToolQuery("lint-arwaky"))
    ).spec
    if spec is None:
        raise AssertionError("lint-arwaky must be in manifest")

    try:
        orch.execute(ToolRequest(ToolsOp("executable_path"), spec=spec))
        assert False, "Should have raised ToolInstallError"
    except ToolInstallError:
        pass


def test_create_tools_feature():
    """IT-TOOLS-011: create_tools_feature returns a wired aggregate."""
    from modules.tools.src.root_tools_container import create_tools_feature
    from modules.shared.src.contract_tools_aggregate import IToolsAggregate

    feature = create_tools_feature()
    assert isinstance(feature, IToolsAggregate)
    # The aggregate's single entry point routes every verb.
    response = feature.execute(ToolRequest(ToolsOp("list")))
    assert isinstance(response, ToolResponse)
    assert len(response.tools) >= 10


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


def test_execute_is_the_only_public_method():
    """IT-TOOLS-015: the aggregate surface has exactly one public method."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    orch = ToolsOrchestrator(registry={})
    for attr in ("list", "resolve", "install", "update", "uninstall", "run",
                 "executable_path"):
        assert not hasattr(orch, attr) or attr in ("execute",), f"unexpected {attr}"
