"""Unit tests for modules/check — test individual functions and methods."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestDocsCheckRunner:
    """Tests for DocsCheckRunner class."""

    def test_init_with_default_root(self):
        """UT-CHECK-001: DocsCheckRunner initializes with default root."""
        from modules.check.src.capabilities_check_docs import DocsCheckRunner

        runner = DocsCheckRunner()
        assert runner._root is not None

    def test_init_with_custom_root(self):
        """UT-CHECK-002: DocsCheckRunner accepts custom root path."""
        from modules.check.src.capabilities_check_docs import DocsCheckRunner

        custom_root = Path("/tmp/test")
        runner = DocsCheckRunner(root=custom_root)
        assert runner._root == custom_root

    def test_audit_method_exists(self):
        """UT-CHECK-003: audit method exists."""
        from modules.check.src.capabilities_check_docs import DocsCheckRunner

        runner = DocsCheckRunner()
        assert hasattr(runner, 'audit')
        assert callable(getattr(runner, 'audit'))

    def test_run_method_exists(self):
        """UT-CHECK-004: run method exists."""
        from modules.check.src.capabilities_check_docs import DocsCheckRunner
        from modules.shared.src.taxonomy_check_vo import CheckScope

        runner = DocsCheckRunner()
        assert hasattr(runner, 'run')
        assert callable(getattr(runner, 'run'))

    def test_name_attribute(self):
        """UT-CHECK-005: name attribute is set correctly."""
        from modules.check.src.capabilities_check_docs import DocsCheckRunner

        runner = DocsCheckRunner()
        assert runner.name == "docs"

    def test_title_attribute(self):
        """UT-CHECK-006: title attribute is set correctly."""
        from modules.check.src.capabilities_check_docs import DocsCheckRunner

        runner = DocsCheckRunner()
        assert "document" in runner.title.lower()


class TestSkillsCheckRunner:
    """Tests for SkillsCheckRunner class."""

    def test_init_with_default_root(self):
        """UT-CHECK-007: SkillsCheckRunner initializes with default root."""
        from modules.check.src.capabilities_check_skills import SkillsCheckRunner

        runner = SkillsCheckRunner()
        assert runner._root is not None
        assert runner._pack is not None

    def test_init_with_custom_root(self):
        """UT-CHECK-008: SkillsCheckRunner accepts custom root path."""
        from modules.check.src.capabilities_check_skills import SkillsCheckRunner

        custom_root = Path("/tmp/test")
        runner = SkillsCheckRunner(root=custom_root)
        assert runner._root == custom_root
        assert runner._pack == custom_root / "skills"

    def test_run_method_exists(self):
        """UT-CHECK-009: run method exists."""
        from modules.check.src.capabilities_check_skills import SkillsCheckRunner
        from modules.shared.src.taxonomy_check_vo import CheckScope

        runner = SkillsCheckRunner()
        assert hasattr(runner, 'run')
        assert callable(getattr(runner, 'run'))

    def test_name_attribute(self):
        """UT-CHECK-010: name attribute is set correctly."""
        from modules.check.src.capabilities_check_skills import SkillsCheckRunner

        runner = SkillsCheckRunner()
        assert runner.name == "skill"


class TestCheckVO:
    """Tests for Check value objects."""

    def test_check_exit_code_creation(self):
        """UT-CHECK-011: CheckExitCode can be created."""
        from modules.shared.src.taxonomy_check_vo import CheckExitCode

        code = CheckExitCode(0)
        assert code == 0

    def test_check_exit_code_nonzero(self):
        """UT-CHECK-012: CheckExitCode works with non-zero values."""
        from modules.shared.src.taxonomy_check_vo import CheckExitCode

        code = CheckExitCode(1)
        assert code == 1

    def test_check_request_with_scope(self):
        """UT-CHECK-013: CheckRequest carries scope."""
        from modules.shared.src.taxonomy_check_vo import CheckRequest, CheckScope

        req = CheckRequest(CheckScope("docs"))
        assert req.scope == "docs"

    def test_check_response_fields(self):
        """UT-CHECK-014: CheckResponse exposes exit_code and summary."""
        from modules.shared.src.taxonomy_check_vo import CheckExitCode, CheckRequest, CheckResponse, CheckSummary, CheckScope

        req = CheckRequest(CheckScope("all"))
        resp = CheckResponse(CheckExitCode(0), CheckSummary("0 findings"))
        assert resp.exit_code == 0
        assert resp.summary == "0 findings"


class TestCheckOrchestrator:
    """Tests for CheckOrchestrator class."""

    def test_init(self):
        """UT-CHECK-015: CheckOrchestrator initializes."""
        from modules.check.src.agent_check_orchestrator import CheckOrchestrator
        from modules.check.src.capabilities_check_docs import DocsCheckRunner

        orch = CheckOrchestrator([DocsCheckRunner()])
        assert orch is not None

    def test_execute_method_exists(self):
        """UT-CHECK-016: execute method exists on the orchestrator."""
        from modules.check.src.agent_check_orchestrator import CheckOrchestrator
        from modules.check.src.capabilities_check_docs import DocsCheckRunner

        orch = CheckOrchestrator([DocsCheckRunner()])
        assert hasattr(orch, 'execute')
        assert callable(getattr(orch, 'execute'))

    def test_execute_dispatches_run(self):
        """UT-CHECK-017: execute dispatches to the runner's run method."""
        from modules.check.src.agent_check_orchestrator import CheckOrchestrator
        from modules.check.src.capabilities_check_docs import DocsCheckRunner
        from modules.shared.src.taxonomy_check_vo import CheckRequest, CheckScope

        runner = DocsCheckRunner()
        orch = CheckOrchestrator([runner])
        with patch.object(runner, "run", return_value=0) as mock_fn:
            result = orch.execute(CheckRequest(CheckScope("docs")))
            mock_fn.assert_called_once()
            assert result is not None

    def test_execute_returns_response(self):
        """UT-CHECK-018: execute returns a CheckResponse."""
        from modules.check.src.agent_check_orchestrator import CheckOrchestrator
        from modules.check.src.capabilities_check_docs import DocsCheckRunner
        from modules.shared.src.taxonomy_check_vo import CheckRequest, CheckResponse, CheckScope

        runner = DocsCheckRunner()
        orch = CheckOrchestrator([runner])
        with patch.object(runner, "run", return_value=0):
            response = orch.execute(CheckRequest(CheckScope("docs")))
        assert isinstance(response, CheckResponse)
        assert hasattr(response, "exit_code")
        assert hasattr(response, "summary")
