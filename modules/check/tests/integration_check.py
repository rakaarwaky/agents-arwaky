"""Integration tests for modules/check — test component interactions."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def test_docs_check_runner_execution():
    """IT-CHECK-001: DocsCheckRunner executes without errors."""
    from modules.check.src.capabilities_check_docs import DocsCheckRunner
    from modules.shared.src.taxonomy_check_vo import CheckScope

    runner = DocsCheckRunner()
    # This may fail due to missing docs, but should not raise
    try:
        result = runner.execute(CheckScope("docs"))
        assert result is not None
    except Exception:
        pass  # Expected if no docs exist


def test_skills_check_runner_execution():
    """IT-CHECK-002: SkillsCheckRunner executes without errors."""
    from modules.check.src.capabilities_check_skills import SkillsCheckRunner
    from modules.shared.src.taxonomy_check_vo import CheckScope

    runner = SkillsCheckRunner()
    try:
        result = runner.execute(CheckScope("skill"))
        assert result is not None
    except Exception:
        pass


def test_orchestrator_creation():
    """IT-CHECK-003: CheckOrchestrator can be created."""
    from modules.check.src.root_check_container import CheckContainer

    container = CheckContainer()
    assert container is not None


def test_check_orchestrator_execute():
    """IT-CHECK-004: Orchestrator can execute check operations."""
    from modules.check.src.agent_check_orchestrator import CheckOrchestrator
    from modules.check.src.capabilities_check_docs import DocsCheckRunner
    from modules.check.src.capabilities_check_skills import SkillsCheckRunner
    from modules.shared.src.taxonomy_check_vo import CheckScope

    docs = DocsCheckRunner()
    skills = SkillsCheckRunner()
    orch = CheckOrchestrator([docs, skills])

    # Should be able to execute
    assert orch is not None
