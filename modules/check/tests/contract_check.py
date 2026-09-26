"""Contract tests for modules/check — verify protocol implementations."""
from __future__ import annotations


def test_check_protocol_exists():
    """CP-CHECK-001: ICheckProtocol exists and can be imported."""
    from modules.shared.src.contract_check_protocol import ICheckProtocol

    assert ICheckProtocol is not None


def test_check_vo_classes_exist():
    """CP-CHECK-002: Check VO classes are defined."""
    from modules.shared.src.taxonomy_check_vo import CheckRequest, CheckResponse, CheckScope

    assert CheckRequest is not None
    assert CheckResponse is not None
    assert CheckScope is not None


def test_docs_check_runner_exists():
    """CP-CHECK-003: DocsCheckRunner class exists."""
    from modules.check.src.capabilities_check_docs import DocsCheckRunner

    assert DocsCheckRunner is not None


def test_skills_check_runner_exists():
    """CP-CHECK-004: SkillsCheckRunner class exists."""
    from modules.check.src.capabilities_check_skills import SkillsCheckRunner

    assert SkillsCheckRunner is not None


def test_check_orchestrator_exists():
    """CP-CHECK-005: CheckOrchestrator class exists."""
    from modules.check.src.agent_check_orchestrator import CheckOrchestrator

    assert CheckOrchestrator is not None


def test_check_runner_implements_protocol():
    """CP-CHECK-006: Check runners implement the rich ICheckProtocol."""
    from modules.check.src.capabilities_check_docs import DocsCheckRunner
    from modules.check.src.capabilities_check_skills import SkillsCheckRunner
    from modules.shared.src.contract_check_protocol import ICheckProtocol

    docs_runner = DocsCheckRunner()
    skills_runner = SkillsCheckRunner()

    assert isinstance(docs_runner, ICheckProtocol)
    assert isinstance(skills_runner, ICheckProtocol)


def test_check_run_method_exists():
    """CP-CHECK-007: Check runners have run method."""
    from modules.check.src.capabilities_check_docs import DocsCheckRunner
    from modules.check.src.capabilities_check_skills import SkillsCheckRunner

    docs = DocsCheckRunner()
    skills = SkillsCheckRunner()

    assert hasattr(docs, 'run')
    assert hasattr(skills, 'run')
    assert callable(getattr(docs, 'run'))
    assert callable(getattr(skills, 'run'))


def test_check_aggregate_declares_only_execute():
    """CP-CHECK-008: the aggregate exposes exactly one abstract method."""
    from modules.shared.src.contract_check_aggregate import ICheckAggregate

    abstract = {
        name
        for name in vars(ICheckAggregate)
        if callable(getattr(ICheckAggregate, name, None))
        and getattr(getattr(ICheckAggregate, name), "__isabstractmethod__", False)
    }
    assert abstract == {"execute"}
