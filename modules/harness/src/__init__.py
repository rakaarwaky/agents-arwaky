"""Harness feature — public symbols.

Re-exports the orchestrator and per-harness connectors so feature
consumers can import from ``modules.harness`` directly. The composition
root (``root_harness_container``) is imported by callers directly, not
re-exported here, to keep the agent/capability package free of a root
re-export cycle (AES205).
"""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator, cmd_connect, cmd_disconnect
from modules.harness.src.capabilities_harness_antigravity import AntigravityConnector
from modules.harness.src.capabilities_harness_grok_build import GrokBuildConnector
from modules.harness.src.capabilities_harness_hermes import HermesConnector
from modules.harness.src.capabilities_harness_opencode import OpencodeConnector
from modules.harness.src.capabilities_harness_qwencode import QwencodeConnector

__all__ = [
    "AntigravityConnector",
    "GrokBuildConnector",
    "HarnessOrchestrator",
    "HermesConnector",
    "OpencodeConnector",
    "QwencodeConnector",
    "cmd_connect",
    "cmd_disconnect",
]
