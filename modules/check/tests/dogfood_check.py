"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_check_pipeline():
    """DOG-CHECK-001: Basic dogfood check for check module."""
    from modules.check.src.capabilities_check_docs import DocsCheckRunner
    from modules.check.src.capabilities_check_skills import SkillsCheckRunner

    docs = DocsCheckRunner()
    skills = SkillsCheckRunner()

    assert hasattr(docs, 'run')
    assert hasattr(skills, 'run')
    assert docs.name == "docs"
    assert skills.name == "skill"
