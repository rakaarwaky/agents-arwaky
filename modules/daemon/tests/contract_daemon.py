"""Contract tests for modules/daemon — verify protocol and class implementations."""
from __future__ import annotations


def test_idaemonprotocol_exists():
    """CP-DAEMON-001: IDaemonProtocol exists as an ABC with rich methods."""
    from modules.shared.src.contract_daemon_protocol import IDaemonProtocol

    assert IDaemonProtocol is not None
    assert hasattr(IDaemonProtocol, '__abstractmethods__')
    for method in ("start", "stop", "restart", "status", "logs",
                   "install_unit", "remove_unit", "unit_status"):
        assert hasattr(IDaemonProtocol, method)


def test_anytype_daemon_manager_class_exists():
    """CP-DAEMON-002: AnytypeDaemonManager class exists."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

    assert AnytypeDaemonManager is not None
    assert hasattr(AnytypeDaemonManager, '__init__')
    assert not hasattr(AnytypeDaemonManager, 'execute')


def test_ninerouter_daemon_manager_class_exists():
    """CP-DAEMON-003: NinerouterDaemonManager class exists."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager

    assert NinerouterDaemonManager is not None
    assert hasattr(NinerouterDaemonManager, '__init__')
    assert not hasattr(NinerouterDaemonManager, 'execute')


def test_anytype_implements_idaemonprotocol():
    """CP-DAEMON-004: AnytypeDaemonManager implements the rich IDaemonProtocol."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
    from modules.shared.src.contract_daemon_protocol import IDaemonProtocol

    manager = AnytypeDaemonManager()
    assert isinstance(manager, IDaemonProtocol)


def test_ninerouter_implements_idaemonprotocol():
    """CP-DAEMON-005: NinerouterDaemonManager implements the rich IDaemonProtocol."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
    from modules.shared.src.contract_daemon_protocol import IDaemonProtocol

    manager = NinerouterDaemonManager()
    assert isinstance(manager, IDaemonProtocol)


def test_anytype_exposes_rich_methods():
    """CP-DAEMON-006: AnytypeDaemonManager exposes rich protocol methods."""
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager

    manager = AnytypeDaemonManager()
    for method in ("start", "stop", "restart", "status", "logs",
                   "install_unit", "remove_unit", "unit_status"):
        assert callable(getattr(manager, method))


def test_ninerouter_exposes_rich_methods():
    """CP-DAEMON-007: NinerouterDaemonManager exposes rich protocol methods."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager

    manager = NinerouterDaemonManager()
    for method in ("start", "stop", "restart", "status", "logs",
                   "install_unit", "remove_unit", "unit_status"):
        assert callable(getattr(manager, method))


def test_orchestrator_class_exists():
    """CP-DAEMON-008: DaemonOrchestrator class exists."""
    from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator

    assert DaemonOrchestrator is not None
    assert hasattr(DaemonOrchestrator, '__init__')
    assert hasattr(DaemonOrchestrator, 'execute')
    # Old named methods are gone.
    assert not hasattr(DaemonOrchestrator, 'list_known')
    assert not hasattr(DaemonOrchestrator, 'start')
    assert not hasattr(DaemonOrchestrator, 'status')


def test_orchestrator_implements_idaemonaggregate():
    """CP-DAEMON-009: DaemonOrchestrator implements IDaemonAggregate."""
    from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
    from modules.shared.src.contract_daemon_aggregate import IDaemonAggregate
    from modules.daemon.src.capabilities_anytype_daemon import AnytypeDaemonManager
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager

    ninerouter = NinerouterDaemonManager()
    anytype = AnytypeDaemonManager()
    orchestrator = DaemonOrchestrator(ninerouter, anytype)
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
