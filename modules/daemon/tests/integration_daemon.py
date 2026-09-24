"""Integration tests for modules/daemon — real wiring and command interactions."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


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
    """IT-DAEMON-002: Orchestrator.start dispatches to AnytypeDaemonManager."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonName

    container = DaemonContainer()
    with patch.object(
        container.anytype, 'execute', return_value=0
    ) as mock_exec:
        result = container.aggregate.start(DaemonName("anytype"))
        mock_exec.assert_called_once_with("start")
        assert result == 0


def test_orchestrator_stop_9router():
    """IT-DAEMON-003: Orchestrator.stop dispatches to NinerouterDaemonManager."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonName

    container = DaemonContainer()
    with patch.object(
        container.ninerouter, 'execute', return_value=0
    ) as mock_exec:
        result = container.aggregate.stop(DaemonName("9router"))
        mock_exec.assert_called_once_with("stop")
        assert result == 0


def test_orchestrator_restart_anytype():
    """IT-DAEMON-004: Orchestrator.restart dispatches to AnytypeDaemonManager."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonName

    container = DaemonContainer()
    with patch.object(
        container.anytype, 'execute', return_value=0
    ) as mock_exec:
        result = container.aggregate.restart(DaemonName("anytype"))
        mock_exec.assert_called_once_with("restart")
        assert result == 0


def test_orchestrator_status_anytype():
    """IT-DAEMON-005: Orchestrator.status returns DaemonStatus."""
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
        container.anytype, 'execute', return_value=expected
    ):
        result = container.aggregate.status(DaemonName("anytype"))
        assert result == expected


def test_orchestrator_logs_9router():
    """IT-DAEMON-006: Orchestrator.logs dispatches to NinerouterDaemonManager."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonName

    container = DaemonContainer()
    with patch.object(
        container.ninerouter, 'execute', return_value=0
    ) as mock_exec:
        result = container.aggregate.logs(DaemonName("9router"))
        mock_exec.assert_called_once_with("logs")
        assert result == 0


def test_orchestrator_install_unit():
    """IT-DAEMON-007: Orchestrator.install_unit dispatches to manager."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonUnit

    container = DaemonContainer()
    with patch.object(
        container.anytype, 'execute', return_value=0
    ) as mock_exec:
        result = container.aggregate.install_unit(DaemonUnit("anytype-daemon.service"))
        mock_exec.assert_called_once_with("install_unit", unit="anytype-daemon.service")
        assert result == 0


def test_orchestrator_remove_unit():
    """IT-DAEMON-008: Orchestrator.remove_unit dispatches to manager."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonUnit

    container = DaemonContainer()
    with patch.object(
        container.ninerouter, 'execute', return_value=0
    ) as mock_exec:
        result = container.aggregate.remove_unit(DaemonUnit("9router.service"))
        mock_exec.assert_called_once_with("remove_unit", unit="9router.service")
        assert result == 0


def test_orchestrator_unit_status():
    """IT-DAEMON-009: Orchestrator.unit_status dispatches to manager."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.taxonomy_daemon_vo import DaemonUnit

    container = DaemonContainer()
    with patch.object(
        container.anytype, 'execute', return_value=0
    ) as mock_exec:
        result = container.aggregate.unit_status(DaemonUnit("anytype-daemon.service"))
        mock_exec.assert_called_once_with("unit_status", unit="anytype-daemon.service")
        assert result == 0


def test_anytype_execute_with_various_ops():
    """IT-DAEMON-010: AnytypeDaemonManager.execute handles multiple ops."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
    from modules.shared.src.taxonomy_daemon_vo import DaemonStatus

    manager = AnytypeDaemonManager()

    ops_to_test = [
        ("start", lambda: patch.object(manager, 'start', return_value=0)),
        ("stop", lambda: patch.object(manager, 'stop', return_value=0)),
        ("restart", lambda: patch.object(manager, 'restart', return_value=0)),
        ("logs", lambda: patch.object(manager, 'logs', return_value=0)),
        ("install_unit", lambda: patch.object(manager, 'install_unit', return_value=0)),
        ("remove_unit", lambda: patch.object(manager, 'remove_unit', return_value=0)),
        ("unit_status", lambda: patch.object(manager, 'unit_status', return_value=0)),
        ("auth-create", lambda: patch.object(manager, 'auth_create', return_value=0)),
        ("auth-key", lambda: patch.object(manager, 'auth_key', return_value=0)),
        ("space-join", lambda: patch.object(manager, 'space_join', return_value=0)),
        ("space-list", lambda: patch.object(manager, 'space_list', return_value=0)),
        ("help", lambda: patch.object(manager, 'help', return_value=0)),
    ]

    for op, patcher in ops_to_test:
        with patcher():
            result = manager.execute(op)
            assert result == 0, f"Expected 0 for op={op}, got {result}"

    # Status op returns DaemonStatus, not 0
    expected = DaemonStatus(
        container_state="running",
        service_state="active",
        api_ready=True,
        data_dir="/test",
        ok=True,
    )
    with patch.object(manager, 'status', return_value=expected):
        result = manager.execute("status")
        assert result == expected


def test_ninerouter_execute_with_various_ops():
    """IT-DAEMON-011: NinerouterDaemonManager.execute handles multiple ops."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
    from modules.shared.src.taxonomy_daemon_vo import DaemonStatus

    manager = NinerouterDaemonManager()

    ops_to_test = [
        ("start", lambda: patch.object(manager, 'start', return_value=0)),
        ("stop", lambda: patch.object(manager, 'stop', return_value=0)),
        ("restart", lambda: patch.object(manager, 'restart', return_value=0)),
        ("logs", lambda: patch.object(manager, 'logs', return_value=0)),
        ("models", lambda: patch.object(manager, 'models', return_value=0)),
        ("install_unit", lambda: patch.object(manager, 'install_unit', return_value=0)),
        ("remove_unit", lambda: patch.object(manager, 'remove_unit', return_value=0)),
        ("unit_status", lambda: patch.object(manager, 'unit_status', return_value=0)),
        ("help", lambda: patch.object(manager, 'help', return_value=0)),
    ]

    for op, patcher in ops_to_test:
        with patcher():
            result = manager.execute(op)
            assert result == 0, f"Expected 0 for op={op}, got {result}"

    # Status op returns DaemonStatus
    expected = DaemonStatus(
        container_state="running",
        service_state="active",
        api_ready=True,
        data_dir="/test",
        ok=True,
    )
    with patch.object(manager, 'status', return_value=expected):
        result = manager.execute("status")
        assert result == expected


def test_full_feature_wiring():
    """IT-DAEMON-012: Full feature wiring from create_daemon_feature."""
    from modules.daemon.src.root_daemon_container import create_daemon_feature
    from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
    from modules.shared.src.taxonomy_daemon_vo import DaemonName

    aggregate = create_daemon_feature()
    assert isinstance(aggregate, IDaemonAggregate)

    # Verify we can call list_known
    known = aggregate.list_known()
    assert len(known) == 2
    assert any(str(name) == "9router" for name in known)
    assert any(str(name) == "anytype" for name in known)


def test_surface_command_integration():
    """IT-DAEMON-013: DaemonAction integrates with DaemonContainer."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.daemon.src.surface_daemon_command import DaemonAction

    container = DaemonContainer()
    action = DaemonAction(container.aggregate)
    assert action is not None
    assert hasattr(action, 'list_known')
    assert hasattr(action, 'start')
    assert hasattr(action, 'stop')


def test_execute_with_name_argument():
    """IT-DAEMON-014: execute passes name argument to capability methods."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

    manager = AnytypeDaemonManager()
    with patch.object(manager, 'auth_create', return_value=0) as mock_auth:
        manager.execute("auth-create", name="test-agent")
        mock_auth.assert_called_once_with("test-agent")

    with patch.object(manager, 'auth_key', return_value=0) as mock_key:
        manager.execute("auth-key", name="my-key")
        mock_key.assert_called_once_with("my-key")


def test_execute_with_unit_argument():
    """IT-DAEMON-015: execute passes unit argument to capability methods."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

    manager = AnytypeDaemonManager()
    with patch.object(manager, 'install_unit', return_value=0) as mock_install:
        manager.execute("install_unit")
        mock_install.assert_called_once()

    with patch.object(manager, 'unit_status', return_value=0) as mock_status:
        manager.execute("unit_status")
        mock_status.assert_called_once()
