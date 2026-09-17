"""Doctor feature — public symbols.

Re-exports the orchestrator, container, diagnostic runners, and surface
entry points so feature consumers can import from ``modules.doctor``
directly.
"""
from __future__ import annotations

from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator
from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner
from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner
from modules.doctor.src.root_doctor_container import DoctorContainer, create_doctor_feature
from modules.doctor.src.surface_doctor_command import cmd_doctor, cmd_status

__all__ = [
    "DoctorContainer",
    "DoctorOrchestrator",
    "EnvDiagnosticRunner",
    "ToolsDiagnosticRunner",
    "cmd_doctor",
    "cmd_status",
    "create_doctor_feature",
]
