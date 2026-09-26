"""Unit tests for modules/service — test individual functions and methods."""
from __future__ import annotations

from unittest.mock import patch

from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
from modules.service.src.capabilities_service_manager import ServiceManager
from modules.shared.src.taxonomy_service_vo import (
    ServiceOp,
    ServiceRequest,
    ServiceTarget,
)


class TestServiceManager:
    """Tests for ServiceManager class."""

    def test_init_creates_manager(self):
        """UT-SERVICE-001: ServiceManager initializes correctly."""
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        assert manager is not None

    def test_status_method_exists(self):
        """UT-SERVICE-003: status method exists."""
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        assert hasattr(manager, 'status')
        assert callable(getattr(manager, 'status'))

    def test_start_method_exists(self):
        """UT-SERVICE-004: start method exists."""
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        assert hasattr(manager, 'start')
        assert callable(getattr(manager, 'start'))

    def test_stop_method_exists(self):
        """UT-SERVICE-005: stop method exists."""
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        assert hasattr(manager, 'stop')
        assert callable(getattr(manager, 'stop'))

    def test_restart_method_exists(self):
        """UT-SERVICE-006: restart method exists."""
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        assert hasattr(manager, 'restart')
        assert callable(getattr(manager, 'restart'))

    def test_logs_method_exists(self):
        """UT-SERVICE-007: logs method exists."""
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        assert hasattr(manager, 'logs')
        assert callable(getattr(manager, 'logs'))

    def test_help_method_exists(self):
        """UT-SERVICE-008: help method exists."""
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        assert hasattr(manager, 'help')
        assert callable(getattr(manager, 'help'))


class TestServiceOrchestrator:
    """Tests for ServiceOrchestrator class."""

    def test_init_creates_orchestrator(self):
        """UT-SERVICE-009: ServiceOrchestrator initializes correctly."""
        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        orch = ServiceOrchestrator(manager)
        assert orch is not None

    def test_execute_status_delegates(self):
        """UT-SERVICE-010: execute dispatches status to the manager."""
        manager = ServiceManager()
        orch = ServiceOrchestrator(manager)
        with patch.object(manager, "status", return_value=0) as mock_fn:
            result = orch.execute(ServiceRequest(ServiceOp("status")))
            mock_fn.assert_called_once()
            assert int(result) == 0

    def test_execute_start_delegates(self):
        """UT-SERVICE-011: execute dispatches start to the manager (never hits live systemctl)."""
        manager = ServiceManager()
        orch = ServiceOrchestrator(manager)
        with patch.object(manager, "start", return_value=0) as mock_fn:
            result = orch.execute(ServiceRequest(ServiceOp("start"), target=ServiceTarget("all")))
            mock_fn.assert_called_once_with(ServiceTarget("all"))
            assert int(result) == 0

    def test_execute_stop_delegates(self):
        """UT-SERVICE-012: execute dispatches stop to the manager (never hits live systemctl)."""
        manager = ServiceManager()
        orch = ServiceOrchestrator(manager)
        with patch.object(manager, "stop", return_value=0) as mock_fn:
            result = orch.execute(ServiceRequest(ServiceOp("stop"), target=ServiceTarget("9router")))
            mock_fn.assert_called_once_with(ServiceTarget("9router"))
            assert int(result) == 0

    def test_execute_restart_delegates(self):
        """UT-SERVICE-013: execute dispatches restart to the manager."""
        manager = ServiceManager()
        orch = ServiceOrchestrator(manager)
        with patch.object(manager, "restart", return_value=0) as mock_fn:
            result = orch.execute(ServiceRequest(ServiceOp("restart")))
            mock_fn.assert_called_once()
            assert int(result) == 0
