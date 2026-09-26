"""Integration tests for modules/service — test component interactions."""
from __future__ import annotations


def test_service_manager_execution():
    """IT-SERVICE-001: ServiceManager status routes through injected aggregate (mocked)."""
    from unittest.mock import MagicMock, patch

    from modules.service.src import capabilities_service_manager as csm
    from modules.service.src.capabilities_service_manager import ServiceManager
    from modules.shared.src.taxonomy_daemon_vo import DaemonName, DaemonOp, DaemonOutcome, DaemonRequest

    manager = ServiceManager()
    mock_agg = MagicMock()
    mock_agg.execute.return_value = DaemonOutcome(success=True, exit_code=0)
    with patch.object(csm, "_DAEMON_AGGREGATE", mock_agg):
        result = manager.status()
        assert result is not None
        assert mock_agg.execute.call_count == 2
        mock_agg.execute.assert_any_call(
            DaemonRequest(DaemonOp("status"), name=DaemonName("9router"))
        )
        mock_agg.execute.assert_any_call(
            DaemonRequest(DaemonOp("status"), name=DaemonName("anytype"))
        )


def test_service_orchestrator_creation():
    """IT-SERVICE-002: ServiceOrchestrator can be created."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
    from modules.service.src.capabilities_service_manager import ServiceManager

    manager = ServiceManager()
    orch = ServiceOrchestrator(manager)
    assert orch is not None


def test_service_container_creation():
    """IT-SERVICE-003: ServiceContainer creates valid aggregate."""
    from modules.service.src.root_service_container import ServiceContainer

    container = ServiceContainer()
    aggregate = container.aggregate
    assert aggregate is not None
