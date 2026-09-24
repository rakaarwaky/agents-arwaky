"""Contract tests for modules/doctor — verify protocol implementations."""
from __future__ import annotations


def test_doctor_protocol_exists():
    """CP-DOCTOR-001: IDoctorProtocol exists and can be imported."""
    from modules.shared.src.contract_doctor_protocol import IDoctorProtocol

    assert IDoctorProtocol is not None


def test_doctor_env_runner_exists():
    """CP-DOCTOR-002: EnvDiagnosticRunner class exists."""
    from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner

    assert EnvDiagnosticRunner is not None


def test_doctor_tools_runner_exists():
    """CP-DOCTOR-003: ToolsDiagnosticRunner class exists."""
    from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

    assert ToolsDiagnosticRunner is not None


def test_doctor_runner_implements_protocol():
    """CP-DOCTOR-004: Doctor runners implement IDoctorProtocol."""
    from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner
    from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner
    from modules.shared.src.contract_doctor_protocol import IDoctorProtocol

    env = EnvDiagnosticRunner()
    tools = ToolsDiagnosticRunner()

    assert isinstance(env, IDoctorProtocol)
    assert isinstance(tools, IDoctorProtocol)


def test_doctor_orchestrator_exists():
    """CP-DOCTOR-005: DoctorOrchestrator class exists."""
    from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator

    assert DoctorOrchestrator is not None


def test_doctor_execute_method_exists():
    """CP-DOCTOR-006: Doctor runners have execute method."""
    from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner
    from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

    env = EnvDiagnosticRunner()
    tools = ToolsDiagnosticRunner()

    assert hasattr(env, 'execute')
    assert hasattr(tools, 'execute')
    assert callable(getattr(env, 'execute'))
    assert callable(getattr(tools, 'execute'))
