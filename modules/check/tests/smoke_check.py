"""Smoke tests for modules/check — fast import and basic checks."""
from __future__ import annotations

import time


def test_import_check_modules():
    """SM-CHECK-001: Check modules can be imported."""
    from modules.check.src import capabilities_check_docs
    from modules.check.src import capabilities_check_skills
    from modules.check.src import agent_check_orchestrator
    from modules.check.src import root_check_container

    assert capabilities_check_docs is not None
    assert capabilities_check_skills is not None
    assert agent_check_orchestrator is not None
    assert root_check_container is not None


def test_check_runners_init_quick():
    """SM-CHECK-002: Check runner initialization is quick."""
    from modules.check.src.capabilities_check_docs import DocsCheckRunner
    from modules.check.src.capabilities_check_skills import SkillsCheckRunner

    start = time.time()
    docs = DocsCheckRunner()
    skills = SkillsCheckRunner()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_orchestrator_init_quick():
    """SM-CHECK-003: Orchestrator initialization is quick."""
    from modules.check.src.agent_check_orchestrator import CheckOrchestrator
    from modules.check.src.capabilities_check_docs import DocsCheckRunner

    start = time.time()
    orch = CheckOrchestrator([DocsCheckRunner()])
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Initialization took {elapsed:.2f}s"


def test_container_creation_quick():
    """SM-CHECK-004: Container creation is quick."""
    from modules.check.src.root_check_container import CheckContainer

    start = time.time()
    container = CheckContainer()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Container creation took {elapsed:.2f}s"
