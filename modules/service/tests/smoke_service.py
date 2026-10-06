"""Smoke tests for modules/service — fast import and basic checks."""
from __future__ import annotations

import time


def test_import_service_modules():
    """SM-SERVICE-001: Service modules can be imported."""
    from modules.service.src import (
        agent_service_orchestrator,
        capabilities_service_manager,
        root_service_container,
    )

    assert capabilities_service_manager is not None
    assert agent_service_orchestrator is not None
    assert root_service_container is not None


def test_service_manager_init_quick():
    """SM-SERVICE-002: ServiceManager initialization is quick."""
    from modules.service.src.capabilities_service_manager import ServiceManager

    start = time.time()
    ServiceManager()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_service_orchestrator_init_quick():
    """SM-SERVICE-003: ServiceOrchestrator initialization is quick."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
    from modules.service.src.capabilities_service_manager import ServiceManager

    start = time.time()
    manager = ServiceManager()
    ServiceOrchestrator(manager)
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_container_creation_quick():
    """SM-SERVICE-004: Container creation is quick."""
    from modules.service.src.root_service_container import ServiceContainer

    start = time.time()
    ServiceContainer()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Container creation took {elapsed:.2f}s"
