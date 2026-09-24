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

    def test_execute_method_exists(self):
        """UT-CHECK-004: execute method exists."""
        from modules.check.src.capabilities_check_docs import DocsCheckRunner
        from modules.shared.src.taxonomy_check_vo import CheckScope

        runner = DocsCheckRunner()
        assert hasattr(runner, 'execute')

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

    def test_name_attribute(self):
        """UT-CHECK-009: name attribute is set correctly."""
        from modules.check.src.capabilities_check_skills import SkillsCheckRunner

        runner = SkillsCheckRunner()
        assert runner.name == "skill"


class TestCheckVO:
    """Tests for Check value objects."""

    def test_check_exit_code_creation(self):
        """UT-CHECK-010: CheckExitCode can be created."""
        from modules.shared.src.taxonomy_check_vo import CheckExitCode

        code = CheckExitCode(0)
        assert code == 0

    def test_check_exit_code_nonzero(self):
        """UT-CHECK-011: CheckExitCode works with non-zero values."""
        from modules.shared.src.taxonomy_check_vo import CheckExitCode

        code = CheckExitCode(1)
        assert code == 1
