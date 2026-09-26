"""Unit tests for modules/doctor — test individual functions and methods."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestEnvDiagnosticRunner:
    """Tests for EnvDiagnosticRunner class."""

    def test_init_creates_runner(self):
        """UT-DOCTOR-001: EnvDiagnosticRunner initializes correctly."""
        from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner

        runner = EnvDiagnosticRunner()
        assert runner is not None

    def test_run_method_exists(self):
        """UT-DOCTOR-002: run method exists."""
        from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner

        runner = EnvDiagnosticRunner()
        assert hasattr(runner, 'run')
        assert callable(getattr(runner, 'run'))

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

    def test_run_method_exists(self):
        """UT-DOCTOR-007: run method exists."""
        from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

        runner = ToolsDiagnosticRunner()
        assert hasattr(runner, 'run')
        assert callable(getattr(runner, 'run'))


class TestDoctorOrchestrator:
    """Tests for the single-execute DoctorOrchestrator dispatch."""

    def _orch(self, env_rc=0, tools_rc=0):
        """Build an orchestrator over two mocked runners."""
        from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator

        env, tools = MagicMock(), MagicMock()
        env.run.return_value = env_rc
        tools.run.return_value = tools_rc
        return DoctorOrchestrator(env, tools), env, tools

    def test_init_creates_orchestrator(self):
        """UT-DOCTOR-008: DoctorOrchestrator initializes correctly."""
        from modules.doctor.src.agent_doctor_orchestrator import DoctorOrchestrator
        from modules.doctor.src.capabilities_doctor_env import EnvDiagnosticRunner
        from modules.doctor.src.capabilities_doctor_tools import ToolsDiagnosticRunner

        orch = DoctorOrchestrator(EnvDiagnosticRunner(), ToolsDiagnosticRunner())
        assert orch is not None

    def test_execute_diagnose_runs_both_runners(self):
        """UT-DOCTOR-009: diagnose dispatches to both runners and ORs the exit codes."""
        from modules.shared.src.taxonomy_common_vo import DoctorOp, DoctorRequest

        orch, env, tools = self._orch(env_rc=0, tools_rc=2)
        response = orch.execute(DoctorRequest(DoctorOp("diagnose")))

        assert env.run.call_count == 1
        assert tools.run.call_count == 1
        assert int(response.exit_code) == 2
        assert response.success is False

    def test_execute_diagnose_passes_flags(self):
        """UT-DOCTOR-010: diagnose forwards the request flags to each runner."""
        from modules.shared.src.taxonomy_common_vo import DoctorFlags, DoctorOp, DoctorRequest

        orch, env, tools = self._orch()
        flags = DoctorFlags({"json": True})
        orch.execute(DoctorRequest(DoctorOp("diagnose"), flags=flags))

        env.run.assert_called_once_with(flags)
        tools.run.assert_called_once_with(flags)

    def test_execute_readiness_runs_tools_only(self):
        """UT-DOCTOR-011: readiness dispatches to the tools runner only."""
        from modules.shared.src.taxonomy_common_vo import DoctorOp, DoctorRequest

        orch, env, tools = self._orch(tools_rc=0)
        response = orch.execute(DoctorRequest(DoctorOp("readiness")))

        assert env.run.call_count == 0
        assert tools.run.call_count == 1
        assert int(response.exit_code) == 0
        assert response.success is True

    def test_execute_report_touches_no_runner(self):
        """UT-DOCTOR-012: report is a no-op at the agent layer (surface renders)."""
        from modules.shared.src.taxonomy_common_vo import DoctorOp, DoctorRequest

        orch, env, tools = self._orch()
        response = orch.execute(DoctorRequest(DoctorOp("report"), report={"a": 1}))

        assert env.run.call_count == 0
        assert tools.run.call_count == 0
        assert int(response.exit_code) == 0
        assert response.report == {"a": 1}

    def test_execute_unknown_op_raises(self):
        """UT-DOCTOR-013: an unknown op is rejected instead of silently ignored."""
        from modules.shared.src.taxonomy_common_vo import DoctorOp, DoctorRequest

        orch, _, _ = self._orch()
        with pytest.raises(ValueError):
            orch.execute(DoctorRequest(DoctorOp("bogus")))
