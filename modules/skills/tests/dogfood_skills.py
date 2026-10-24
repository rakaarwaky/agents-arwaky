"""Dogfood tests — runs against the live repo skill pack."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_skills_list():
    """DOG-SKILLS-001: listing the real repo pack works end to end."""
    from modules.skills.src.capabilities_skills_index_builder import SkillsIndexBuilder

    rows = list(SkillsIndexBuilder().list_skills())
    assert rows, "expected the repo skill pack to be non-empty"
    assert all(r.name for r in rows)


@pytest.mark.dogfood
def test_dogfood_skills_show():
    """DOG-SKILLS-002: reading a real SKILL.md works end to end."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery
    from modules.skills.src.capabilities_skills_index_builder import (
        SkillsIndexBuilder,
    )
    from modules.skills.src.capabilities_skills_pack_reader import SkillsPackReader

    rows = list(SkillsIndexBuilder().list_skills())
    content = SkillsPackReader().show_skill(SkillQuery(rows[0].name))
    assert content is not None
    assert "name:" in content


@pytest.mark.dogfood
def test_dogfood_validate_live_pack_is_deterministic():
    """DOG-SKILLS-003: validating the live pack is stable and self-consistent.

    Deliberately does not assert a clean pack: what the live tree contains
    (including categories mounted from submodules) is the pack owner's
    business, and pinning zero issues would make this test a second,
    hidden content gate. It asserts instead that two runs agree, that the
    exit code tracks the unfiltered issue total, and that every reported
    issue carries a locator and a message — the invariants the CLI relies
    on.
    """
    from modules.shared.src.skills.taxonomy_skills_vo import SkillsRequest
    from modules.skills.src.root_skills_container import default_aggregate

    first = default_aggregate().execute(SkillsRequest(op="validate"))
    second = default_aggregate().execute(SkillsRequest(op="validate"))

    assert first.report is not None and second.report is not None
    assert first.report.issues == second.report.issues
    assert first.exit_code == (1 if first.report.issue_count else 0)
    for issue in first.report.issues:
        assert issue.message
        assert issue.locator
