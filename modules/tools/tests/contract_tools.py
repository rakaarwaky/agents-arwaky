"""Contract tests for modules/tools — prove protocol/interface implementations exist."""
from __future__ import annotations


def test_contract_tools_protocol_exists():
    """CP-TOOLS-001: IToolsProtocol exists and is abstract."""
    from modules.shared.src.contract_tools_protocol import IToolsProtocol

    assert IToolsProtocol is not None
    assert hasattr(IToolsProtocol, "execute")
    assert getattr(IToolsProtocol, "execute") is not None


def test_installer_capability_implements_protocol():
    """CP-TOOLS-002: InstallerCapability implements IToolsProtocol."""
    from modules.shared.src.contract_tools_protocol import IToolsProtocol
    from modules.tools.src.capabilities_tools_installer import InstallerCapability

    assert issubclass(InstallerCapability, IToolsProtocol)


def test_updater_capability_implements_protocol():
    """CP-TOOLS-003: UpdaterCapability implements IToolsProtocol."""
    from modules.shared.src.contract_tools_protocol import IToolsProtocol
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability

    assert issubclass(UpdaterCapability, IToolsProtocol)


def test_uninstaller_capability_implements_protocol():
    """CP-TOOLS-004: UninstallerCapability implements IToolsProtocol."""
    from modules.shared.src.contract_tools_protocol import IToolsProtocol
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

    assert issubclass(UninstallerCapability, IToolsProtocol)


def test_runner_capability_implements_protocol():
    """CP-TOOLS-005: RunnerCapability implements IToolsProtocol."""
    from modules.shared.src.contract_tools_protocol import IToolsProtocol
    from modules.tools.src.capabilities_tools_runner import RunnerCapability

    assert issubclass(RunnerCapability, IToolsProtocol)


def test_orchestrator_implements_aggregate():
    """CP-TOOLS-006: ToolsOrchestrator implements IToolsAggregate."""
    from modules.shared.src.contract_tools_aggregate import IToolsAggregate
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    assert issubclass(ToolsOrchestrator, IToolsAggregate)


def test_installer_has_execute_method():
    """CP-TOOLS-007: InstallerCapability.execute exists."""
    from modules.tools.src.capabilities_tools_installer import InstallerCapability

    assert callable(getattr(InstallerCapability, "execute", None))


def test_updater_has_execute_method():
    """CP-TOOLS-008: UpdaterCapability.execute exists."""
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability

    assert callable(getattr(UpdaterCapability, "execute", None))


def test_uninstaller_has_execute_method():
    """CP-TOOLS-009: UninstallerCapability.execute exists."""
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

    assert callable(getattr(UninstallerCapability, "execute", None))


def test_runner_has_execute_method():
    """CP-TOOLS-010: RunnerCapability.execute exists."""
    from modules.tools.src.capabilities_tools_runner import RunnerCapability

    assert callable(getattr(RunnerCapability, "execute", None))


def test_installer_has_install_method():
    """CP-TOOLS-011: InstallerCapability.install exists."""
    from modules.tools.src.capabilities_tools_installer import InstallerCapability

    assert callable(getattr(InstallerCapability, "install", None))


def test_updater_has_update_method():
    """CP-TOOLS-012: UpdaterCapability.update exists."""
    from modules.tools.src.capabilities_tools_updater import UpdaterCapability

    assert callable(getattr(UpdaterCapability, "update", None))


def test_uninstaller_has_uninstall_method():
    """CP-TOOLS-013: UninstallerCapability.uninstall exists."""
    from modules.tools.src.capabilities_tools_uninstaller import UninstallerCapability

    assert callable(getattr(UninstallerCapability, "uninstall", None))


def test_runner_has_run_method():
    """CP-TOOLS-014: RunnerCapability.run exists."""
    from modules.tools.src.capabilities_tools_runner import RunnerCapability

    assert callable(getattr(RunnerCapability, "run", None))


def test_orchestrator_has_required_methods():
    """CP-TOOLS-015: ToolsOrchestrator has all aggregate methods."""
    from modules.tools.src.agent_tools_orchestrator import ToolsOrchestrator

    assert hasattr(ToolsOrchestrator, "list")
    assert hasattr(ToolsOrchestrator, "resolve")
    assert hasattr(ToolsOrchestrator, "install")
    assert hasattr(ToolsOrchestrator, "update")
    assert hasattr(ToolsOrchestrator, "uninstall")
    assert hasattr(ToolsOrchestrator, "run")
    assert hasattr(ToolsOrchestrator, "executable_path")


def test_adapter_facade_implements_protocol():
    """CP-TOOLS-016: ToolAdapterFacade implements IToolsProtocol."""
    from modules.shared.src.contract_tools_protocol import IToolsProtocol
    from modules.tools.src.capabilities_tools_adapter import ToolAdapterFacade

    assert issubclass(ToolAdapterFacade, IToolsProtocol)


def test_error_classes_are_defined():
    """CP-TOOLS-017: Domain error classes exist."""
    from modules.shared.src.taxonomy_common_error import (
        ToolInstallError,
        ToolUpdateError,
        ToolUninstallError,
    )

    assert ToolInstallError is not None
    assert ToolUpdateError is not None
    assert ToolUninstallError is not None


def test_result_vo_classes_exist():
    """CP-TOOLS-018: Result VOs are defined."""
    from modules.shared.src.taxonomy_common_vo import (
        InstallResult,
        UpdateResult,
        UninstallResult,
    )

    assert InstallResult is not None
    assert UpdateResult is not None
    assert UninstallResult is not None
