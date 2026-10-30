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
        from modules.service.src.capabilities_service_inspect import ServiceInspect

        inspect_cap = ServiceInspect()
        assert hasattr(inspect_cap, 'status')
        assert callable(inspect_cap.status)

    def test_logs_method_exists(self):
        """UT-SERVICE-007: logs method exists on inspect."""
        from modules.service.src.capabilities_service_inspect import ServiceInspect

        inspect_cap = ServiceInspect()
        assert hasattr(inspect_cap, 'logs')
        assert callable(inspect_cap.logs)

    def test_help_method_exists(self):
        """UT-SERVICE-008: help method exists on inspect."""
        from modules.service.src.capabilities_service_inspect import ServiceInspect

        inspect_cap = ServiceInspect()
        assert hasattr(inspect_cap, 'help')
        assert callable(inspect_cap.help)


class TestServiceOrchestrator:
    """Tests for ServiceOrchestrator class."""

    def test_init_creates_orchestrator(self):
        """UT-SERVICE-009: ServiceOrchestrator initializes correctly."""
        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.service.src.capabilities_service_inspect import ServiceInspect
        from modules.service.src.capabilities_service_manager import ServiceControl

        control = ServiceControl()
        inspect_cap = ServiceInspect()
        orch = ServiceOrchestrator(control, inspect_cap)
        assert orch is not None

    def test_execute_status_delegates(self):
        """UT-SERVICE-010: execute dispatches status to inspect without host I/O."""
        from unittest.mock import MagicMock

        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.shared.src.service.taxonomy_service_vo import (
            ServiceOp,
            ServiceRequest,
        )

        control = MagicMock()
        inspect_cap = MagicMock()
        inspect_cap.status.return_value = 0
        orch = ServiceOrchestrator(control, inspect_cap)

        result = orch.execute(ServiceRequest(ServiceOp("status")))

        inspect_cap.status.assert_called_once_with()
        control.start.assert_not_called()
        assert result == 0

    def test_execute_start_delegates(self):
        """UT-SERVICE-011: execute dispatches start to control without host I/O."""
        from unittest.mock import MagicMock

        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.shared.src.service.taxonomy_service_vo import (
            ServiceOp,
            ServiceRequest,
        )

        control = MagicMock()
        control.start.return_value = 0
        inspect_cap = MagicMock()
        orch = ServiceOrchestrator(control, inspect_cap)

        result = orch.execute(ServiceRequest(ServiceOp("start")))

        control.start.assert_called_once()
        inspect_cap.status.assert_not_called()
        assert result == 0

    def test_execute_stop_delegates(self):
        """UT-SERVICE-012: execute dispatches stop to control without host I/O."""
        from unittest.mock import MagicMock

        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.shared.src.service.taxonomy_service_vo import (
            ServiceOp,
            ServiceRequest,
        )

        control = MagicMock()
        control.stop.return_value = 0
        inspect_cap = MagicMock()
        orch = ServiceOrchestrator(control, inspect_cap)

        result = orch.execute(ServiceRequest(ServiceOp("stop")))

        control.stop.assert_called_once()
        assert result == 0

    def test_execute_restart_delegates(self):
        """UT-SERVICE-013: execute dispatches restart to control without host I/O."""
        from unittest.mock import MagicMock

        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.shared.src.service.taxonomy_service_vo import (
            ServiceOp,
            ServiceRequest,
        )

        control = MagicMock()
        control.restart.return_value = 0
        inspect_cap = MagicMock()
        orch = ServiceOrchestrator(control, inspect_cap)

        result = orch.execute(ServiceRequest(ServiceOp("restart")))

        control.restart.assert_called_once()
        assert result == 0

class TestNineRouterServiceTarget:
    """The 9router service target coexists with the OmniRoute one."""

    def test_target_constant_exists(self):
        """UT-SERVICE-014: TARGET_9ROUTER is a sibling of TARGET_OMNIROUTE."""
        from modules.shared.src.service.taxonomy_service_vo import (
            TARGET_9ROUTER,
            TARGET_OMNIROUTE,
        )

        assert str(TARGET_9ROUTER) == "9router"
        assert str(TARGET_OMNIROUTE) == "omniroute"

    def test_target_reexported_from_package(self):
        """UT-SERVICE-015: modules.shared.src.service re-exports TARGET_9ROUTER."""
        from modules.shared.src.service import TARGET_9ROUTER

        assert str(TARGET_9ROUTER) == "9router"

    def test_contract_exposes_target_9router(self):
        """UT-SERVICE-016: the protocol contract publishes TARGET_9ROUTER."""
        from modules.shared.src.service import contract_service_protocol as contract

        assert "TARGET_9ROUTER" in contract.__all__
        assert str(contract._layer_symbols["TARGET_9ROUTER"]) == "9router"

    def test_execute_stop_dispatches_9router_target(self):
        """UT-SERVICE-017: execute(stop) forwards ServiceTarget('9router') verbatim."""
        from unittest.mock import MagicMock

        from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
        from modules.shared.src.service.taxonomy_service_vo import (
            ServiceOp,
            ServiceRequest,
            ServiceTarget,
        )

        control = MagicMock()
        control.stop.return_value = 0
        inspect_cap = MagicMock()
        orch = ServiceOrchestrator(control, inspect_cap)

        result = orch.execute(
            ServiceRequest(ServiceOp("stop"), target=ServiceTarget("9router"))
        )

        control.stop.assert_called_once_with(ServiceTarget("9router"))
        assert result == 0

    def test_logs_default_stays_omniroute(self):
        """UT-SERVICE-018: logs() keeps OmniRoute as the documented default."""
        import inspect

        from modules.shared.src.service import contract_service_protocol as contract

        sig = inspect.signature(contract.IServiceInspectProtocol.logs)
        assert str(sig.parameters["target"].default) == "omniroute"
