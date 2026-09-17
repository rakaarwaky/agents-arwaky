"""Harness feature — public symbols.

Re-exports the orchestrator, container, per-harness connectors, shared
helpers, and surface entry points so feature consumers can import from
``modules.harness`` directly.
"""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator
from modules.harness.src.capabilities_harness_antigravity import AntigravityConnector
from modules.harness.src.capabilities_harness_grok_build import GrokBuildConnector
from modules.harness.src.capabilities_harness_hermes import HermesConnector
from modules.harness.src.capabilities_harness_opencode import OpencodeConnector
from modules.harness.src.capabilities_harness_qwencode import QwencodeConnector
from modules.harness.src.root_harness_container import HarnessContainer, create_harness_feature
from modules.harness.src.surface_harness_command import cmd_connect, cmd_disconnect

__all__ = [
    "AntigravityConnector",
    "GrokBuildConnector",
    "HarnessContainer",
    "HarnessOrchestrator",
    "HermesConnector",
    "OpencodeConnector",
    "QwencodeConnector",
    "cmd_connect",
    "cmd_disconnect",
    "create_harness_feature",
]
