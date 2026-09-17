"""Doctor feature package — environment diagnostics + tool readiness.

Public re-exports: orchestrator + container.
"""
from __future__ import annotations

from modules.doctor.src import (
    DoctorContainer,
    DoctorOrchestrator,
    create_doctor_feature,
)

__all__ = [
    "DoctorContainer",
    "DoctorOrchestrator",
    "create_doctor_feature",
]
