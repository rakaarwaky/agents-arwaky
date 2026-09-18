"""Harness feature package — connect agent harnesses (Antigravity, Hermes, OpenCode, Qwen Code, Grok Build).

Public re-exports: orchestrator + container.
"""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator, cmd_connect, cmd_disconnect
from modules.harness.src.root_harness_container import HarnessContainer, create_harness_feature

__all__ = [
    "HarnessContainer",
    "HarnessOrchestrator",
    "cmd_connect",
    "cmd_disconnect",
    "create_harness_feature",
]
