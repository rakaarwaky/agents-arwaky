"""Smoke tests for modules/daemon — fast import and initialization checks."""
from __future__ import annotations

import time


def test_import_daemon_module():
    """SM-DAEMON-001: modules.daemon can be imported."""
    import modules.daemon
    assert modules.daemon is not None


def test_import_daemon_capabilities():
    """SM-DAEMON-002: daemon capability modules can be imported."""
    from modules.daemon.src import (
        capabilities_9router_daemon,
        capabilities_omniroute_daemon,
    )
    assert capabilities_omniroute_daemon is not None
    assert capabilities_9router_daemon is not None


def test_import_daemon_orchestrator():
    """SM-DAEMON-003: daemon orchestrator module can be imported."""
    from modules.daemon.src import agent_daemon_orchestrator
    assert agent_daemon_orchestrator is not None


def test_import_daemon_container():
    """SM-DAEMON-004: daemon container module can be imported."""
    from modules.daemon.src import root_daemon_container
    assert root_daemon_container is not None


def test_import_daemon_surface():
    """SM-DAEMON-005: daemon surface module can be imported."""
    from modules.cli.src import surface_daemon_command
    assert surface_daemon_command is not None


def test_import_daemon_protocol():
    """SM-DAEMON-006: daemon protocol contract can be imported."""
    from modules.shared.src.daemon import (
        contract_daemon_aggregate,
        contract_daemon_protocol,
    )
    assert contract_daemon_protocol is not None
    assert contract_daemon_aggregate is not None


def test_import_daemon_vo():
    """SM-DAEMON-007: daemon value objects can be imported."""
    from modules.shared.src.daemon import taxonomy_daemon_vo
    assert taxonomy_daemon_vo is not None


def test_omniroute_manager_instantiates():
    """SM-DAEMON-009: OmnirouteDaemonManager instantiates quickly."""
    from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager

    start = time.time()
    manager = OmnirouteDaemonManager()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"
    assert repr(manager) == "OmnirouteDaemonManager()"


def test_ninerouter_manager_instantiates():
    """SM-DAEMON-009b: NinerouterDaemonManager instantiates quickly."""
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager

    start = time.time()
    manager = NinerouterDaemonManager()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"
    assert repr(manager) == "NinerouterDaemonManager()"


def test_orchestrator_instantiates():
    """SM-DAEMON-010: DaemonOrchestrator instantiates quickly."""
    from modules.daemon.src.agent_daemon_orchestrator import DaemonOrchestrator
    from modules.daemon.src.capabilities_9router_daemon import NinerouterDaemonManager
    from modules.daemon.src.capabilities_omniroute_daemon import OmnirouteDaemonManager

    start = time.time()
    omniroute = OmnirouteDaemonManager()
    ninerouter = NinerouterDaemonManager()
    orchestrator = DaemonOrchestrator(omniroute, ninerouter)
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"
    assert repr(orchestrator) == "DaemonOrchestrator()"


def test_container_instantiates():
    """SM-DAEMON-011: DaemonContainer instantiates quickly."""
    from modules.daemon.src.root_daemon_container import DaemonContainer

    start = time.time()
    container = DaemonContainer()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"
    assert container.aggregate is not None


def test_create_feature_quickly():
    """SM-DAEMON-012: create_daemon_feature completes within 1 second."""
    from modules.daemon.src.root_daemon_container import create_daemon_feature

    start = time.time()
    result = create_daemon_feature()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Feature creation took {elapsed:.2f}s"
    assert result is not None
