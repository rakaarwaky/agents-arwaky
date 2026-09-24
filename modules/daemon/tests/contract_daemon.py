"""Contract tests for modules/daemon — verify protocol and class implementations."""
from __future__ import annotations


def test_idaemonprotocol_exists():
    """CP-DAEMON-001: IDaemonProtocol exists as an ABC."""
    from modules.shared.src.contract_daemon_protocol import IDaemonProtocol

    assert IDaemonProtocol is not None
    assert hasattr(IDaemonProtocol, 'execute')
    assert hasattr(IDaemonProtocol, '__abstractmethods__')


def test_anytype_daemon_manager_class_exists():
    """CP-DAEMON-002: AnytypeDaemonManager class exists."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

    assert AnytypeDaemonManager is not None
    assert hasattr(AnytypeDaemonManager, '__init__')
    assert hasattr(AnytypeDaemonManager, 'execute')


def test_podman_daemon_manager_class_exists():
    """CP-DAEMON-003: PodmanDaemonManager class exists."""
    from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

    assert PodmanDaemonManager is not None
    assert hasattr(PodmanDaemonManager, '__init__')
    assert hasattr(PodmanDaemonManager, 'execute')


def test_anytype_implements_idaemonprotocol():
    """CP-DAEMON-004: AnytypeDaemonManager implements IDaemonProtocol."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
    from modules.shared.src.contract_daemon_protocol import IDaemonProtocol

    manager = AnytypeDaemonManager()
    assert isinstance(manager, IDaemonProtocol)


def test_podman_implements_idaemonprotocol():
    """CP-DAEMON-005: PodmanDaemonManager implements IDaemonProtocol."""
    from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager
    from modules.shared.src.contract_daemon_protocol import IDaemonProtocol

    manager = PodmanDaemonManager()
    assert isinstance(manager, IDaemonProtocol)


def test_anytype_execute_method_exists():
    """CP-DAEMON-006: AnytypeDaemonManager has execute method."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

    manager = AnytypeDaemonManager()
    assert callable(manager.execute)


def test_podman_execute_method_exists():
    """CP-DAEMON-007: PodmanDaemonManager has execute method."""
    from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

    manager = PodmanDaemonManager()
    assert callable(manager.execute)


def test_orchestrator_class_exists():
    """CP-DAEMON-008: DaemonOrchestrator class exists."""
    from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator

    assert DaemonOrchestrator is not None
    assert hasattr(DaemonOrchestrator, '__init__')
    assert hasattr(DaemonOrchestrator, 'list_known')


def test_orchestrator_implements_idaemonaggregate():
    """CP-DAEMON-009: DaemonOrchestrator implements IDaemonAggregate."""
    from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
    from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
    from modules.daemon.src.capabilities_omniroute_daemon import PodmanDaemonManager

    omniroute = PodmanDaemonManager()
    anytype = AnytypeDaemonManager()
    orchestrator = DaemonOrchestrator(omniroute, anytype)
    assert isinstance(orchestrator, IDaemonAggregate)


def test_container_class_exists():
    """CP-DAEMON-010: DaemonContainer class exists."""
    from modules.daemon.src.root_daemon_container import DaemonContainer

    assert DaemonContainer is not None
    assert hasattr(DaemonContainer, '__init__')
    assert hasattr(DaemonContainer, 'aggregate')


def test_container_wires_correctly():
    """CP-DAEMON-011: DaemonContainer returns an IDaemonAggregate."""
    from modules.daemon.src.root_daemon_container import DaemonContainer
    from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate

    container = DaemonContainer()
    assert isinstance(container.aggregate, IDaemonAggregate)


def test_create_daemon_feature_function_exists():
    """CP-DAEMON-012: create_daemon_feature function exists and returns aggregate."""
    from modules.daemon.src.root_daemon_container import create_daemon_feature
    from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate

    result = create_daemon_feature()
    assert isinstance(result, IDaemonAggregate)


def test_daemon_value_objects_exist():
    """CP-DAEMON-013: Daemon value objects exist and are instantiable."""
    from modules.shared.src.taxonomy_daemon_vo import (
        DaemonName,
        DaemonOp,
        DaemonStatus,
        DaemonUnit,
        ExitCode,
    )

    assert DaemonName is not None
    assert DaemonOp is not None
    assert DaemonUnit is not None
    assert ExitCode is not None

    name = DaemonName("test")
    op = DaemonOp("start")
    unit = DaemonUnit("test.service")
    code = ExitCode(0)

    assert str(name) == "test"
    assert str(op) == "start"
    assert str(unit) == "test.service"
    assert code == 0

    status = DaemonStatus(
        container_state="stopped",
        service_state="inactive",
        api_ready=False,
        data_dir="/tmp",
        ok=False,
    )
    assert status.container_state == "stopped"
    assert status.api_ready is False


def test_surface_command_exists():
    """CP-DAEMON-014: surface_daemon_command module exports DaemonAction."""
    from modules.daemon.src.surface_daemon_command import DaemonAction

    assert DaemonAction is not None
    assert hasattr(DaemonAction, '__init__')
