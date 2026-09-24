"""Unit tests for modules/doctor — test individual functions and methods."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestEnvDiagnosticRunner:
    """Tests for EnvDiagnosticRunner class."""

    def test_init_creates_runner(self):
        """UT-DOCTOR-001: EnvDiagnosticRunner initializes correctly."""
        from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner

        runner = EnvDiagnosticRunner()
        assert runner is not None

    def test_execute_method_exists(self):
        """UT-DOCTOR-002: execute method exists."""
        from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner

        runner = EnvDiagnosticRunner()
        assert hasattr(runner, 'execute')
        assert callable(getattr(runner, 'execute'))

    def test_check_toolchain_method_exists(self):
        """UT-DOCTOR-003: _check_toolchain method exists."""
        from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner

        runner = EnvDiagnosticRunner()
        assert hasattr(runner, '_check_toolchain')
        assert callable(getattr(runner, '_check_toolchain'))

    def test_required_toolchain_defined(self):
        """UT-DOCTOR-004: REQUIRED toolchain tuple is defined."""
        from modules.doctor.src.capabilities_doctor_env import REQUIRED

        assert isinstance(REQUIRED, tuple)
        assert "git" in REQUIRED
        assert "jq" in REQUIRED
        assert "curl" in REQUIRED
        assert "python3" in REQUIRED

    def test_optional_toolchain_defined(self):
        """UT-DOCTOR-005: OPTIONAL toolchain tuple is defined."""
        from modules.doctor.src.capabilities_doctor_env import OPTIONAL

        assert isinstance(OPTIONAL, tuple)
        assert "cargo" in OPTIONAL
        assert "uv" in OPTIONAL


class TestToolsDiagnosticRunner:
    """Tests for ToolsDiagnosticRunner class."""

    def test_init_creates_runner(self):
        """UT-DOCTOR-006: ToolsDiagnosticRunner initializes correctly."""
        from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

        runner = ToolsDiagnosticRunner()
        assert runner is not None

    def test_execute_method_exists(self):
        """UT-DOCTOR-007: execute method exists."""
        from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

        runner = ToolsDiagnosticRunner()
        assert hasattr(runner, 'execute')
        assert callable(getattr(runner, 'execute'))
