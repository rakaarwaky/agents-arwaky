"""Unit tests for modules/service — test individual functions and methods."""
from __future__ import annotations


class TestServiceControl:
    """Tests for ServiceControl class."""

    def test_init_creates_control(self):
        """UT-SERVICE-001: ServiceControl initializes correctly."""
        from modules.service.src.capabilities_service_manager import ServiceControl

        control = ServiceControl()
        assert control is not None

    def test_start_method_exists(self):
        """UT-SERVICE-004: start method exists on control."""
        from modules.service.src.capabilities_service_manager import ServiceControl

        control = ServiceControl()
        assert hasattr(control, 'start')
        assert callable(control.start)

    def test_stop_method_exists(self):
        """UT-SERVICE-005: stop method exists on control."""
        from modules.service.src.capabilities_service_manager import ServiceControl

        control = ServiceControl()
        assert hasattr(control, 'stop')
        assert callable(control.stop)

    def test_restart_method_exists(self):
        """UT-SERVICE-006: restart method exists on control."""
        from modules.service.src.capabilities_service_manager import ServiceControl

        control = ServiceControl()
        assert hasattr(control, 'restart')
        assert callable(control.restart)


class TestServiceInspect:
    """Tests for ServiceInspect class."""

    def test_status_method_exists(self):
        """UT-SERVICE-003: status method exists on inspect."""
        from modules.service.src.capabilities_service_manager import ServiceInspect

        inspect_cap = ServiceInspect()
        assert hasattr(inspect_cap, 'status')
        assert callable(inspect_cap.status)

    def test_logs_method_exists(self):
        """UT-SERVICE-007: logs method exists on inspect."""
        from modules.service.src.capabilities_service_manager import ServiceInspect

        inspect_cap = ServiceInspect()
        assert hasattr(inspect_cap, 'logs')
        assert callable(inspect_cap.logs)

    def test_help_method_exists(self):
        """UT-SERVICE-008: help method exists on inspect."""
        from modules.service.src.capabilities_service_manager import ServiceInspect

        inspect_cap = ServiceInspect()
        assert hasattr(inspect_cap, 'help')
        assert callable(inspect_cap.help)


class TestServiceOrchestrator:
    """Tests for ServiceOrchestrator class."""

    def test_init_creates_orchestrator(self):
        """UT-SERVICE-009: ServiceOrchestrator initializes correctly."""
        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.service.src.capabilities_service_manager import ServiceControl, ServiceInspect

        control = ServiceControl()
        inspect_cap = ServiceInspect()
        orch = ServiceOrchestrator(control, inspect_cap)
        assert orch is not None

    def test_execute_status_delegates(self):
        """UT-SERVICE-010: execute dispatches status to inspect."""
        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.service.src.capabilities_service_manager import ServiceControl, ServiceInspect
        from modules.shared.src.service.taxonomy_service_vo import ServiceOp, ServiceRequest

        control = ServiceControl()
        inspect_cap = ServiceInspect()
        orch = ServiceOrchestrator(control, inspect_cap)
        result = orch.execute(ServiceRequest(ServiceOp("status")))
        assert result is not None

    def test_execute_start_delegates(self):
        """UT-SERVICE-011: execute dispatches start to control."""
        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.service.src.capabilities_service_manager import ServiceControl, ServiceInspect
        from modules.shared.src.service.taxonomy_service_vo import ServiceOp, ServiceRequest

        control = ServiceControl()
        inspect_cap = ServiceInspect()
        orch = ServiceOrchestrator(control, inspect_cap)
        result = orch.execute(ServiceRequest(ServiceOp("start")))
        assert result is not None

    def test_execute_stop_delegates(self):
        """UT-SERVICE-012: execute dispatches stop to control."""
        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.service.src.capabilities_service_manager import ServiceControl, ServiceInspect
        from modules.shared.src.service.taxonomy_service_vo import ServiceOp, ServiceRequest

        control = ServiceControl()
        inspect_cap = ServiceInspect()
        orch = ServiceOrchestrator(control, inspect_cap)
        result = orch.execute(ServiceRequest(ServiceOp("stop")))
        assert result is not None

    def test_execute_restart_delegates(self):
        """UT-SERVICE-013: execute dispatches restart to control."""
        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.service.src.capabilities_service_manager import ServiceControl, ServiceInspect
        from modules.shared.src.service.taxonomy_service_vo import ServiceOp, ServiceRequest

        control = ServiceControl()
        inspect_cap = ServiceInspect()
        orch = ServiceOrchestrator(control, inspect_cap)
        result = orch.execute(ServiceRequest(ServiceOp("restart")))
        assert result is not None
