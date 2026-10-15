"""Contract tests for modules/service — verify protocol implementations."""
from __future__ import annotations


def test_service_protocol_exists():
    """CP-SERVICE-001: IServiceProtocol exists and can be imported."""
    from modules.shared.src.service.contract_service_protocol import (
        IServiceControlProtocol,
        IServiceInspectProtocol,
    )

    assert IServiceControlProtocol is not None
    assert IServiceInspectProtocol is not None


def test_service_aggregate_exists():
    """CP-SERVICE-002: IServiceAggregate exists and can be imported."""
    from modules.shared.src.service.contract_service_aggregate import IServiceAggregate

    assert IServiceAggregate is not None


def test_service_control_exists():
    """CP-SERVICE-003: ServiceControl class exists."""
    from modules.service.src.capabilities_service_manager import ServiceControl

    assert ServiceControl is not None


def test_service_inspect_exists():
    """CP-SERVICE-004: ServiceInspect class exists."""
    from modules.service.src.capabilities_service_inspect import ServiceInspect

    assert ServiceInspect is not None


def test_service_orchestrator_exists():
    """CP-SERVICE-005: ServiceOrchestrator class exists."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator

    assert ServiceOrchestrator is not None


def test_service_control_implements_protocol():
    """CP-SERVICE-006: ServiceControl implements IServiceControlProtocol."""
    from modules.service.src.capabilities_service_manager import ServiceControl
    from modules.shared.src.service.contract_service_protocol import (
        IServiceControlProtocol,
    )

    control = ServiceControl()
    assert isinstance(control, IServiceControlProtocol)
    for method in ("start", "stop", "restart"):
        assert callable(getattr(control, method))


def test_service_inspect_implements_protocol():
    """CP-SERVICE-007: ServiceInspect implements IServiceInspectProtocol."""
    from modules.service.src.capabilities_service_inspect import ServiceInspect
    from modules.shared.src.service.contract_service_protocol import (
        IServiceInspectProtocol,
    )

    inspect_cap = ServiceInspect()
    assert isinstance(inspect_cap, IServiceInspectProtocol)
    for method in ("status", "logs", "help"):
        assert callable(getattr(inspect_cap, method))


def test_service_orchestrator_implements_aggregate():
    """CP-SERVICE-008: ServiceOrchestrator implements the single-execute aggregate."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
    from modules.service.src.capabilities_service_inspect import ServiceInspect
    from modules.service.src.capabilities_service_manager import ServiceControl
    from modules.shared.src.service.contract_service_aggregate import IServiceAggregate

    control = ServiceControl()
    inspect_cap = ServiceInspect()
    orch = ServiceOrchestrator(control, inspect_cap)
    assert isinstance(orch, IServiceAggregate)