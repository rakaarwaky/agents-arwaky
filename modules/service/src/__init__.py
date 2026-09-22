"""Service feature — public symbols.

Re-exports the orchestrator, container, and surface entry points so
feature consumers can import from ``modules.service`` directly.
"""
from __future__ import annotations

from modules.service.src.agent_service_orchestrator import ServiceOrchestrator
from modules.service.src.capabilities_service_manager import ServiceManager
from modules.service.src.root_service_container import ServiceContainer, create_service_feature
from modules.service.src.surface_service_command import cmd_service

__all__ = [
    "ServiceContainer",
    "ServiceManager",
    "ServiceOrchestrator",
    "cmd_service",
    "create_service_feature",
]
