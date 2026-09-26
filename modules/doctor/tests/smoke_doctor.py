"""Smoke tests for modules/doctor — fast import and basic checks."""
from __future__ import annotations

import time


def test_import_doctor_modules():
    """SM-DOCTOR-001: Doctor modules can be imported."""
    from modules.doctor.src import capabilities_doctor_env
    from modules.doctor.src import capabilities_doctor_tools
    from modules.doctor.src import agent_doctor_orchestrator
    from modules.doctor.src import root_doctor_container

    assert capabilities_doctor_env is not None
    assert capabilities_doctor_tools is not None
    assert agent_doctor_orchestrator is not None
    assert root_doctor_container is not None


def test_env_runner_init_quick():
    """SM-DOCTOR-002: EnvDiagnosticRunner initialization is quick."""
    from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner

    start = time.time()
    runner = EnvDiagnosticRunner()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_tools_runner_init_quick():
    """SM-DOCTOR-003: ToolsDiagnosticRunner initialization is quick."""
    from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

    start = time.time()
    runner = ToolsDiagnosticRunner()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"
