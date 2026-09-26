"""Integration tests for modules/daemon — real wiring and command interactions."""
from __future__ import annotations

from unittest.mock import patch

from modules.shared.src.taxonomy_daemon_vo import (
    DaemonName,
    DaemonOp,
    DaemonRequest,
    DaemonStatus,
    DaemonUnit,
)


def test_container_creation():
    """IT-DAEMON-001: DaemonContainer creates working orchestrator."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
    from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate

    container = DaemonContainer()
    assert container.aggregate is not None
    assert isinstance(container.aggregate, IDaemonAggregate)
    assert isinstance(container.aggregate, DaemonOrchestrator)


def test_orchestrator_start_anytype():
    """IT-DAEMON-002: Orchestrator.execute(start) routes to AnytypeDaemonManager.start."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.anytype, 'start', return_value=ExitCode(0)
    ) as mock_start:
        result = container.aggregate.execute(DaemonRequest(DaemonOp("start"), name=DaemonName("anytype")))
        mock_start.assert_called_once()
        assert result.exit_code == 0


def test_orchestrator_stop_9router():
    """IT-DAEMON-003: Orchestrator.execute(stop) routes to NinerouterDaemonManager.stop."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.ninerouter, 'stop', return_value=ExitCode(0)
    ) as mock_stop:
        result = container.aggregate.execute(DaemonRequest(DaemonOp("stop"), name=DaemonName("9router")))
        mock_stop.assert_called_once()
        assert result.exit_code == 0


def test_orchestrator_restart_anytype():
    """IT-DAEMON-004: Orchestrator.execute(restart) routes to AnytypeDaemonManager.restart."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.anytype, 'restart', return_value=ExitCode(0)
    ) as mock_restart:
        result = container.aggregate.execute(DaemonRequest(DaemonOp("restart"), name=DaemonName("anytype")))
        mock_restart.assert_called_once()
        assert result.exit_code == 0


def test_orchestrator_status_anytype():
    """IT-DAEMON-005: Orchestrator.execute(status) returns a DaemonStatus."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonName, DaemonStatus

    container = DaemonContainer()
    expected = DaemonStatus(
        container_state="running",
        service_state="active",
        api_ready=True,
        data_dir="/test",
        ok=True,
    )
    with patch.object(
        container.anytype, 'status', return_value=expected
    ):
        result = container.aggregate.execute(DaemonRequest(DaemonOp("status"), name=DaemonName("anytype")))
        assert result.status == expected


def test_orchestrator_logs_9router():
    """IT-DAEMON-006: Orchestrator.execute(logs) routes to NinerouterDaemonManager.logs."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.ninerouter, 'logs', return_value=ExitCode(0)
    ) as mock_logs:
        result = container.aggregate.execute(DaemonRequest(DaemonOp("logs"), name=DaemonName("9router")))
        mock_logs.assert_called_once()
        assert result.exit_code == 0


def test_orchestrator_install_unit():
    """IT-DAEMON-007: Orchestrator.execute(install_unit) routes to manager.install_unit."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.anytype, 'install_unit', return_value=ExitCode(0)
    ) as mock_install:
        result = container.aggregate.execute(
            DaemonRequest(DaemonOp("install_unit"), unit=DaemonUnit("anytype-daemon.service"))
        )
        mock_install.assert_called_once_with(DaemonUnit("anytype-daemon.service"))
        assert result.exit_code == 0


def test_orchestrator_remove_unit():
    """IT-DAEMON-008: Orchestrator.execute(remove_unit) routes to manager.remove_unit."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.ninerouter, 'remove_unit', return_value=ExitCode(0)
    ) as mock_remove:
        result = container.aggregate.execute(
            DaemonRequest(DaemonOp("remove_unit"), unit=DaemonUnit("9router.service"))
        )
        mock_remove.assert_called_once_with(DaemonUnit("9router.service"))
        assert result.exit_code == 0


def test_orchestrator_unit_status():
    """IT-DAEMON-009: Orchestrator.execute(unit_status) routes to manager.unit_status."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import ExitCode

    container = DaemonContainer()
    with patch.object(
        container.anytype, 'unit_status', return_value=ExitCode(0)
    ) as mock_us:
        result = container.aggregate.execute(
            DaemonRequest(DaemonOp("unit_status"), unit=DaemonUnit("anytype-daemon.service"))
        )
        mock_us.assert_called_once_with(DaemonUnit("anytype-daemon.service"))
        assert result.exit_code == 0


def test_anytype_rich_protocol_methods():
    """IT-DAEMON-010: AnytypeDaemonManager has all rich protocol methods."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
    from modules.shared.src.contract_daemon_protocol import IDaemonProtocol
    from modules.shared.src.taxonomy_daemon_vo import DaemonStatus

    manager = AnytypeDaemonManager()
    assert isinstance(manager, IDaemonProtocol)
    assert not hasattr(manager, "execute")

    # Each method is callable (may raise at runtime; we only verify the shape).
    for method in ("start", "stop", "restart", "logs",
                   "install_unit", "remove_unit", "unit_status"):
        assert callable(getattr(manager, method))

    with patch.object(manager, "status", return_value=DaemonStatus(
        container_state="stopped", service_state="inactive", api_ready=False,
        data_dir="", ok=False,
    )):
        result = manager.status()
        assert isinstance(result, DaemonStatus)


def test_ninerouter_rich_protocol_methods():
    """IT-DAEMON-011: NinerouterDaemonManager has all rich protocol methods."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
    from modules.shared.src.contract_daemon_protocol import IDaemonProtocol
    from modules.shared.src.taxonomy_daemon_vo import DaemonStatus

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


def test_full_feature_wiring():
    """IT-DAEMON-012: Full feature wiring from create_daemon_feature."""
    from modules.daemon.src.root_daemon_container import create_daemon_feature
    from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
    from modules.shared.src.taxonomy_daemon_vo import DaemonName, DaemonOp, DaemonRequest

    aggregate = create_daemon_feature()
    assert isinstance(aggregate, IDaemonAggregate)

    # The orchestrator exposes .known, not list_known.
    assert len(aggregate.known) == 2
    names = {str(n) for n in aggregate.known}
    assert "9router" in names
    assert "anytype" in names

    # execute still routes: a real status call returns an outcome, whatever the daemon state.
    result = aggregate.execute(
        DaemonRequest(DaemonOp("status"), name=DaemonName("anytype"))
    )
    assert result.exit_code in (0, 1)
    assert result.status is not None


def test_surface_command_integration():
    """IT-DAEMON-013: DaemonAction integrates with DaemonContainer via execute."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.daemon.src.surface_daemon_command import DaemonAction
    from modules.shared.src.taxonomy_daemon_vo import DaemonOp, DaemonRequest

    container = DaemonContainer()
    action = DaemonAction(container.aggregate)
    assert action is not None
    assert callable(action.execute)
    # Old named methods are gone from the aggregate surface.
    assert not hasattr(action, 'list_known')
    assert not hasattr(action, 'start')
    assert not hasattr(action, 'stop')


def test_execute_with_name_argument():
    """IT-DAEMON-014: execute passes name into the request; manager receives start()."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonName, DaemonOp, DaemonRequest

    container = DaemonContainer()
    with patch.object(container.anytype, "start", return_value=0) as mock_start:
        result = container.aggregate.execute(
            DaemonRequest(DaemonOp("start"), name=DaemonName("anytype"))
        )
        mock_start.assert_called_once()
        assert result.exit_code == 0


def test_execute_with_unit_argument():
    """IT-DAEMON-015: execute passes unit into the request; manager receives unit argument."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonOp, DaemonRequest, DaemonUnit

    container = DaemonContainer()
    with patch.object(
        container.anytype, 'install_unit', return_value=0
    ) as mock_install:
        result = container.aggregate.execute(
            DaemonRequest(DaemonOp("install_unit"), unit=DaemonUnit("anytype-daemon.service"))
        )
        mock_install.assert_called_once_with(DaemonUnit("anytype-daemon.service"))
        assert result.exit_code == 0
