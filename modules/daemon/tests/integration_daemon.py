"""Integration tests for modules/daemon — real wiring and command interactions."""
from __future__ import annotations

from unittest.mock import patch

from modules.shared.src.daemon.taxonomy_daemon_vo import (
    DaemonName,
    DaemonOp,
    DaemonRequest,
    DaemonUnit,
)


def test_container_creation():
    """IT-DAEMON-001: DaemonContainer creates working orchestrator."""
    from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.daemon.contract_daemon_aggregate import IDaemonAggregate

    container = DaemonContainer()
    assert container.aggregate is not None
    assert isinstance(container.aggregate, IDaemonAggregate)
    assert isinstance(container.aggregate, DaemonOrchestrator)


def test_orchestrator_stop_omniroute():
    """IT-DAEMON-003: Orchestrator.execute(stop) routes to OmnirouteDaemonManager.stop."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.daemon.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.omniroute, 'stop', return_value=ExitCode(0)
    ) as mock_stop:
        result = container.aggregate.execute(DaemonRequest(DaemonOp("stop"), name=DaemonName("omniroute")))
        mock_stop.assert_called_once()
        assert result.exit_code == 0


def test_orchestrator_logs_omniroute():
    """IT-DAEMON-006: Orchestrator.execute(logs) routes to OmnirouteDaemonManager.logs."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.daemon.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.omniroute, 'logs', return_value=ExitCode(0)
    ) as mock_logs:
        result = container.aggregate.execute(DaemonRequest(DaemonOp("logs"), name=DaemonName("omniroute")))
        mock_logs.assert_called_once()
        assert result.exit_code == 0


def test_orchestrator_remove_unit():
    """IT-DAEMON-008: Orchestrator.execute(remove_unit) routes to manager.remove_unit."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.daemon.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.omniroute, 'remove_unit', return_value=ExitCode(0)
    ) as mock_remove:
        result = container.aggregate.execute(
            DaemonRequest(DaemonOp("remove_unit"), unit=DaemonUnit("omniroute.service"))
        )
        mock_remove.assert_called_once_with(DaemonUnit("omniroute.service"))
        assert result.exit_code == 0


def test_omniroute_rich_protocol_methods():
    """IT-DAEMON-011: OmnirouteDaemonManager has all rich protocol methods."""
    from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager
    from modules.shared.src.daemon.contract_daemon_protocol import IDaemonProtocol
    from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonStatus

    manager = OmnirouteDaemonManager()
    assert isinstance(manager, IDaemonProtocol)
    assert not hasattr(manager, "execute")

    for method in ("start", "stop", "restart", "logs",
                   "install_unit", "remove_unit", "unit_status"):
        assert callable(getattr(manager, method))

    with patch.object(manager, "status", return_value=DaemonStatus(
        container_state="stopped", service_state="inactive", api_ready=False,
        data_dir="", ok=False,
    )):
        result = manager.status()
        assert isinstance(result, DaemonStatus)


def test_surface_command_integration():
    """IT-DAEMON-013: DaemonAction integrates with DaemonContainer via execute."""
    from modules.cli.src.surface_daemon_command import DaemonAction
    from modules.daemon.src.root_daemon_container import DaemonContainer

    container = DaemonContainer()
    action = DaemonAction(container.aggregate)
    assert action is not None
    assert callable(action.execute)
    # Old named methods are gone from the aggregate surface.
    assert not hasattr(action, 'list_known')
    assert not hasattr(action, 'start')
    assert not hasattr(action, 'stop')


def test_orchestrator_stop_9router():
    """IT-DAEMON-003b: Orchestrator.execute(stop) routes to NinerouterDaemonManager.stop."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.daemon.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.ninerouter, 'stop', return_value=ExitCode(0)
    ) as mock_stop, patch.object(
        container.omniroute, 'stop', return_value=ExitCode(0)
    ) as mock_omni:
        result = container.aggregate.execute(
            DaemonRequest(DaemonOp("stop"), name=DaemonName("9router"))
        )
        mock_stop.assert_called_once()
        mock_omni.assert_not_called()
        assert result.exit_code == 0


def test_orchestrator_logs_9router():
    """IT-DAEMON-006b: Orchestrator.execute(logs) routes to NinerouterDaemonManager.logs."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.daemon.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.ninerouter, 'logs', return_value=ExitCode(0)
    ) as mock_logs:
        result = container.aggregate.execute(
            DaemonRequest(DaemonOp("logs"), name=DaemonName("9router"))
        )
        mock_logs.assert_called_once()
        assert result.exit_code == 0


def test_orchestrator_remove_unit_9router():
    """IT-DAEMON-008b: unit ops resolve 9router.service to the 9router manager."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.daemon.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.ninerouter, 'remove_unit', return_value=ExitCode(0)
    ) as mock_remove, patch.object(
        container.omniroute, 'remove_unit', return_value=ExitCode(0)
    ) as mock_omni:
        result = container.aggregate.execute(
            DaemonRequest(DaemonOp("remove_unit"), unit=DaemonUnit("9router.service"))
        )
        mock_remove.assert_called_once_with(DaemonUnit("9router.service"))
        mock_omni.assert_not_called()
        assert result.exit_code == 0


def test_ninerouter_rich_protocol_methods():
    """IT-DAEMON-011b: NinerouterDaemonManager has all rich protocol methods."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
    from modules.shared.src.daemon.contract_daemon_protocol import IDaemonProtocol
    from modules.shared.src.daemon.taxonomy_daemon_vo import DaemonStatus

    manager = NinerouterDaemonManager()
    assert isinstance(manager, IDaemonProtocol)
    assert not hasattr(manager, "execute")

    for method in ("start", "stop", "restart", "logs",
                   "install_unit", "remove_unit", "unit_status"):
        assert callable(getattr(manager, method))

    with patch.object(manager, "status", return_value=DaemonStatus(
        container_state="stopped", service_state="inactive", api_ready=False,
        data_dir="", ok=False,
    )):
        result = manager.status()
        assert isinstance(result, DaemonStatus)
