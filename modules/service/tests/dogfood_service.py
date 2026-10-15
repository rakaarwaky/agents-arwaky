"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_service_pipeline():
    """DOG-SERVICE-001: Basic dogfood check for service module."""
    from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
    from modules.service.src.capabilities_service_inspect import ServiceInspect
    from modules.service.src.capabilities_service_manager import ServiceControl

    control = ServiceControl()
    inspect_cap = ServiceInspect()
    orch = ServiceOrchestrator(control, inspect_cap)

    assert hasattr(inspect_cap, 'status')
    assert hasattr(orch, 'execute')