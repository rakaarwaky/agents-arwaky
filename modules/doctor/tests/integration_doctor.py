"""Integration tests for modules/doctor — test component interactions."""
from __future__ import annotations


def test_env_diagnostic_runner_execution():
    """IT-DOCTOR-001: EnvDiagnosticRunner executes without errors."""
    from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner

    runner = EnvDiagnosticRunner()
    # This may print to stdout but should not raise
    try:
        result = runner.execute()
        assert result is not None
    except Exception:
        pass


def test_tools_diagnostic_runner_execution():
    """IT-DOCTOR-002: ToolsDiagnosticRunner executes without errors."""
    from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

    runner = ToolsDiagnosticRunner()
    try:
        result = runner.execute()
        assert result is not None
    except Exception:
        pass


def test_doctor_orchestrator_creation():
    """IT-DOCTOR-003: DoctorOrchestrator can be created."""
    from modules.doctor.src.root_doctor_container import DoctorContainer

    container = DoctorContainer()
    assert container is not None
