"""Unit tests for modules/service — test individual functions and methods."""
from __future__ import annotations

from unittest.mock import patch

from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
from modules.service.src.capabilities_service_manager import ServiceManager


class TestServiceManager:
    """Tests for ServiceManager class."""

    def test_init_creates_manager(self):
        """UT-SERVICE-001: ServiceManager initializes correctly."""
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        assert manager is not None

    def test_execute_method_exists(self):
        """UT-SERVICE-002: execute method exists."""
        from modules.service.src.capabilities_service_manager import ServiceManager

        manager = ServiceManager()
        assert hasattr(manager, 'execute')
        assert callable(getattr(manager, 'execute'))

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

    def test_status_delegates(self):
        """UT-SERVICE-010: status delegates to manager."""
        manager = ServiceManager()
        orch = ServiceOrchestrator(manager)
        with patch.object(manager, "execute", return_value=0) as mock_exec:
            result = orch.status()
            mock_exec.assert_called_once()
            assert result == 0

    def test_start_delegates(self):
        """UT-SERVICE-011: start delegates to manager (never hits live systemctl)."""
        manager = ServiceManager()
        orch = ServiceOrchestrator(manager)
        with patch.object(manager, "execute", return_value=0) as mock_exec:
            result = orch.start()
            mock_exec.assert_called_once()
            assert result == 0

    def test_stop_delegates(self):
        """UT-SERVICE-012: stop delegates to manager (never hits live systemctl)."""
        manager = ServiceManager()
        orch = ServiceOrchestrator(manager)
        with patch.object(manager, "execute", return_value=0) as mock_exec:
            result = orch.stop()
            mock_exec.assert_called_once()
            assert result == 0

    def test_restart_delegates(self):
        """UT-SERVICE-013: restart delegates to manager (never hits live systemctl)."""
        manager = ServiceManager()
        orch = ServiceOrchestrator(manager)
        with patch.object(manager, "execute", return_value=0) as mock_exec:
            result = orch.restart()
            mock_exec.assert_called_once()
            assert result == 0
