"""Contract tests for modules/tools — prove protocol/interface implementations exist."""
from __future__ import annotations


def test_protocol_classes_exist():
    """CP-TOOLS-001: the five tools capability protocol classes exist and are ABCs."""
    from modules.shared.src.contract_tools_protocol import (
        IToolsAdapterProtocol,
        IToolsInstallerProtocol,
        IToolsRunnerProtocol,
        IToolsUninstallerProtocol,
        IToolsUpdaterProtocol,
    )

    for protocol in (
        IToolsAdapterProtocol,
        IToolsInstallerProtocol,
        IToolsRunnerProtocol,
        IToolsUninstallerProtocol,
        IToolsUpdaterProtocol,
    ):
        assert protocol.__abstractmethods__, f"{protocol.__name__} declares no methods"


def test_protocol_methods_are_named():
    """CP-TOOLS-002: each protocol declares named methods, never an execute(op) bag."""
    from modules.shared.src.contract_tools_protocol import (
        IToolsAdapterProtocol,
        IToolsInstallerProtocol,
        IToolsRunnerProtocol,
        IToolsUninstallerProtocol,
        IToolsUpdaterProtocol,
    )

    expected = {
        IToolsInstallerProtocol: {"install"},
        IToolsUpdaterProtocol: {"update"},
        IToolsUninstallerProtocol: {"uninstall"},
        IToolsRunnerProtocol: {"run", "discover"},
        IToolsAdapterProtocol: {"satisfied", "is_pin_satisfied", "owned_paths", "install", "update"},
    }
    for protocol, methods in expected.items():
        assert protocol.__abstractmethods__ == frozenset(methods)
        assert not hasattr(protocol, "execute")


def test_installer_capability_implements_protocol():
    """CP-TOOLS-003: InstallerCapability implements IToolsInstallerProtocol."""
    from modules.shared.src.contract_tools_protocol import IToolsInstallerProtocol
    from modules.tools.src.capabilities_tools_installer import InstallerCapability

    assert issubclass(InstallerCapability, IToolsInstallerProtocol)


def test_updater_capability_implements_protocol():
    """CP-TOOLS-004: UpdaterCapability implements IToolsUpdaterProtocol."""
    from modules.shared.src.contract_tools_protocol import IToolsUpdaterProtocol
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability

    assert issubclass(UpdaterCapability, IToolsUpdaterProtocol)


def test_uninstaller_capability_implements_protocol():
    """CP-TOOLS-005: UninstallerCapability implements IToolsUninstallerProtocol."""
    from modules.shared.src.contract_tools_protocol import IToolsUninstallerProtocol
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

    assert issubclass(UninstallerCapability, IToolsUninstallerProtocol)


def test_runner_capability_implements_protocol():
    """CP-TOOLS-006: RunnerCapability implements IToolsRunnerProtocol."""
    from modules.shared.src.contract_tools_protocol import IToolsRunnerProtocol
    from modules.tools.src.capabilities_tools_runner import RunnerCapability

    assert issubclass(RunnerCapability, IToolsRunnerProtocol)


def test_orchestrator_implements_aggregate():
    """CP-TOOLS-007: ToolsOrchestrator implements IToolsAggregate."""
    from modules.shared.src.contract_tools_aggregate import IToolsAggregate
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    assert issubclass(ToolsOrchestrator, IToolsAggregate)


def test_capabilities_have_no_execute_bag():
    """CP-TOOLS-008: no tools capability exposes the execute(op) dispatch bag."""
    from modules.tools.src.capabilities_tools_installer import InstallerCapability
    from modules.tools.src.capabilities_tools_runner import RunnerCapability
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability

    for cls in (InstallerCapability, UpdaterCapability, UninstallerCapability, RunnerCapability):
        assert not hasattr(cls, "execute")


def test_capabilities_implement_whole_protocol():
    """CP-TOOLS-009: every capability instantiates — no partial implementation."""
    from modules.shared.src.contract_tools_protocol import (
        IToolsRunnerProtocol,
        IToolsUninstallerProtocol,
    )
    from modules.tools.src.capabilities_tools_installer import InstallerCapability
    from modules.tools.src.capabilities_tools_runner import RunnerCapability
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability

    pairs = (
        (InstallerCapability, "install"),
        (UpdaterCapability, "update"),
        (UninstallerCapability, "uninstall"),
    )
    for cls, method in pairs:
        instance = cls()
        assert callable(getattr(instance, method))

    runner = RunnerCapability()
    assert isinstance(runner, IToolsRunnerProtocol)
    assert callable(runner.run)
    assert callable(runner.discover)
    assert isinstance(UninstallerCapability(), IToolsUninstallerProtocol)
