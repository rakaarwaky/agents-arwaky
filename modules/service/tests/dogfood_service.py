"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_service_pipeline():
    """DOG-SERVICE-001: Basic dogfood check for service module."""
    from modules.service.src.capabilities_service_manager import ServiceManager
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator

    manager = ServiceManager()
    orch = ServiceOrchestrator(manager)

    assert hasattr(manager, 'execute')
    assert hasattr(orch, 'status')
