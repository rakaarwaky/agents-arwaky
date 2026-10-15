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


def test_service_manager_exists():
    """CP-SERVICE-003: ServiceManager class exists."""

    assert ServiceManager is not None


def test_service_orchestrator_exists():
    """CP-SERVICE-004: ServiceOrchestrator class exists."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator

    assert ServiceOrchestrator is not None


def test_service_manager_implements_protocol():
    """CP-SERVICE-005: ServiceManager implements the rich IServiceProtocol."""
    from modules.service.src.capabilities_service_manager import (
        ServiceControl,
        ServiceInspect,
    )
    from modules.shared.src.service.contract_service_protocol import (
        IServiceControlProtocol,
        IServiceInspectProtocol,
    )

    control = ServiceControl()
    inspect_cap = ServiceInspect()
    assert isinstance(manager, (IServiceControlProtocol, IServiceInspectProtocol))
    for method in ("status", "start", "stop", "restart", "logs", "help"):
        assert callable(getattr(manager, method))


def test_service_orchestrator_implements_aggregate():
    """CP-SERVICE-006: ServiceOrchestrator implements the single-execute aggregate."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
    from modules.service.src.capabilities_service_manager import (
        ServiceControl,
        ServiceInspect,
    )
    from modules.shared.src.service.contract_service_aggregate import IServiceAggregate

    control = ServiceControl()
    inspect_cap = ServiceInspect()
    orch = ServiceOrchestrator(control, inspect)
    assert isinstance(orch, IServiceAggregate)
    assert callable(orch.execute)


def test_service_aggregate_declares_only_execute():
    """CP-SERVICE-007: the aggregate exposes exactly one abstract method."""
    from modules.shared.src.service.contract_service_aggregate import IServiceAggregate

    abstract = {
        name
        for name in vars(IServiceAggregate)
        if callable(getattr(IServiceAggregate, name, None))
        and getattr(getattr(IServiceAggregate, name), "__isabstractmethod__", False)
    }
    assert abstract == {"execute"}
