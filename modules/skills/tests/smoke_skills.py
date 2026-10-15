"""Smoke tests for modules/skills — fast import and basic checks."""
from __future__ import annotations

import time


def test_import_skills_modules():
    """SM-SKILLS-001: skills modules can be imported."""
    from modules.skills.src import (
        agent_skills_orchestrator,
        capabilities_skills_index_builder,
        root_skills_container,
    )

    assert agent_skills_orchestrator is not None
    assert capabilities_skills_index_builder is not None
    assert root_skills_container is not None


def test_default_aggregate_quick():
    """SM-SKILLS-002: default_aggregate creation is quick."""
    from modules.skills.src.root_skills_container import default_aggregate

    start = time.time()
    aggregate = default_aggregate()
    elapsed = time.time() - start

    assert elapsed < 5.0, f"Creation took {elapsed:.2f}s"
    assert aggregate is not None


def test_list_skills_quick():
    """SM-SKILLS-003: list_skills returns a sequence of records."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillsRequest
    from modules.skills.src.root_skills_container import default_aggregate

    aggregate = default_aggregate()
    result = aggregate.execute(SkillsRequest(op="list"))
    assert result.ok
    assert isinstance(result.records, tuple)
