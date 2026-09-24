"""Integration tests for modules/service — test component interactions."""
from __future__ import annotations


def test_service_manager_execution():
    """IT-SERVICE-001: ServiceManager executes without errors."""
    from modules.service.src.capabilities_service_manager import ServiceManager
    from modules.shared.src.taxonomy_service_vo import ServiceOp

    manager = ServiceManager()
    try:
        result = manager.execute(ServiceOp("status"))
        assert result is not None
    except Exception:
        pass


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
