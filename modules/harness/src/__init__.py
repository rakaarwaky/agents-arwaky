"""Harness feature — public symbols.

Re-exports the orchestrator, the three business-action capabilities, the
CLI surface, and the leaf adapters so feature consumers can import from
``modules.harness`` directly. The composition root (``root_harness_container``)
is imported by callers directly, not re-exported here, to keep the
agent/capability package free of a root re-export cycle (AES205).
"""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator
from modules.harness.src.capabilities_harness_connector import HarnessConnector
from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector
from modules.harness.src.capabilities_harness_skills import HarnessSkills
from modules.harness.src.surface_harness_command import (
    cmd_connect,
    cmd_disconnect,
    main,
)

__all__ = [
    "HarnessConnector",
    "HarnessDisconnector",
    "HarnessOrchestrator",
    "HarnessSkills",
    "cmd_connect",
    "cmd_disconnect",
    "main",
]
