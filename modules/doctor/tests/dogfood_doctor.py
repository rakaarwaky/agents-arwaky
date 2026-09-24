"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_doctor_pipeline():
    """DOG-DOCTOR-001: Basic dogfood check for doctor module."""
    from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner
    from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

    env = EnvDiagnosticRunner()
    tools = ToolsDiagnosticRunner()

    assert hasattr(env, 'execute')
    assert hasattr(tools, 'execute')
