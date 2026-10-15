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
