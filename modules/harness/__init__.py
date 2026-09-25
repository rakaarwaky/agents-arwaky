"""Harness feature package — connect agent harnesses (Hermes, OpenCode, Grok Build).

Public re-exports: orchestrator + CLI surface. The composition root
(``root_harness_container``) is imported by callers directly, not re-exported
here, to keep the package free of a root re-export cycle (AES205).
"""
from __future__ import annotations

from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator
from modules.harness.src.surface_harness_command import cmd_connect, cmd_disconnect

__all__ = [
    "HarnessOrchestrator",
    "cmd_connect",
    "cmd_disconnect",
]
