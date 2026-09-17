"""Check feature package — repo integrity gates (JSON, Python, docs, skills, shell).

Public re-exports: orchestrator + container.
"""
from __future__ import annotations

from modules.check.src import (
    CheckContainer,
    CheckOrchestrator,
    create_check_feature,
)

__all__ = [
    "CheckContainer",
    "CheckOrchestrator",
    "create_check_feature",
]
