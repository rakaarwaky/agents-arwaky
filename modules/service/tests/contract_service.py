"""Contract tests for modules/service — verify protocol implementations."""
from __future__ import annotations


def test_service_protocol_exists():
    """CP-SERVICE-001: IServiceProtocol exists and can be imported."""
    from modules.shared.src.contract_service_protocol import IServiceProtocol

    assert IServiceProtocol is not None


def test_service_aggregate_exists():
    """CP-SERVICE-002: IServiceAggregate exists and can be imported."""
    from modules.shared.src.contract_service_aggregate import IServiceAggregate

    assert IServiceAggregate is not None


def test_service_manager_exists():
    """CP-SERVICE-003: ServiceManager class exists."""
    from modules.service.src.capabilities_service_manager import ServiceManager

    assert ServiceManager is not None


def test_service_orchestrator_exists():
    """CP-SERVICE-004: ServiceOrchestrator class exists."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator

    assert ServiceOrchestrator is not None


def test_service_manager_implements_protocol():
    """CP-SERVICE-005: ServiceManager implements IServiceProtocol."""
    from modules.service.src.capabilities_service_manager import ServiceManager
    from modules.shared.src.contract_service_protocol import IServiceProtocol

    manager = ServiceManager()
    assert isinstance(manager, IServiceProtocol)


def test_service_orchestrator_implements_aggregate():
    """CP-SERVICE-006: ServiceOrchestrator implements IServiceAggregate."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
    from modules.service.src.capabilities_service_manager import ServiceManager
    from modules.shared.src.contract_service_aggregate import IServiceAggregate

    manager = ServiceManager()
    orch = ServiceOrchestrator(manager)
    assert isinstance(orch, IServiceAggregate)
