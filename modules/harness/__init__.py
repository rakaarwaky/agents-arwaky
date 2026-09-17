"""Harness feature package — connect agent harnesses (Antigravity, Hermes, OpenCode, Qwen Code, Grok Build).

Public re-exports: orchestrator + container.
"""
from __future__ import annotations

from modules.harness.src import (
    HarnessContainer,
    HarnessOrchestrator,
    create_harness_feature,
)

__all__ = [
    "HarnessContainer",
    "HarnessOrchestrator",
    "create_harness_feature",
]
