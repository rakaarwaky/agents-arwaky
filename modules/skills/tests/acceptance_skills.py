"""Acceptance tests — map 1:1 to business requirements (FRD/PRD IDs)."""
from __future__ import annotations

from pathlib import Path


def _make_pack(tmp_path: Path) -> Path:
    pack = tmp_path / "skills"
    (pack / "web" / "fetch-mcp").mkdir(parents=True)
    (pack / "web" / "fetch-mcp" / "SKILL.md").write_text(
        "---\nname: fetch-mcp\ndescription: Scrapes web to markdown.\n---\n\n# Fetch\n",
        encoding="utf-8",
    )
    return pack


def test_acceptance_fr_skill_discovery(tmp_path: Path):
    """AC-SKILLS-001: FR-003 — every skill in the pack is discoverable."""
    from modules.skills.src.capabilities_skills_index_builder import (
    SkillsIndexBuilder,
)

    rows = list(SkillsIndexBuilder(_make_pack(tmp_path)).list_skills())
    assert [r.name for r in rows] == ["fetch-mcp"]


def test_acceptance_fr_skill_lookup(tmp_path: Path):
    """AC-SKILLS-002: FR-003 — a discovered skill's content is retrievable."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery
    from modules.skills.src.capabilities_skills_index_builder import (
    SkillsPackReader,
)

    pack = _make_pack(tmp_path)
    content = SkillsPackReader(pack).show_skill(SkillQuery("fetch-mcp"))
    assert content is not None
    assert "fetch-mcp" in content
    assert "Scrapes web to markdown" in content


def test_acceptance_fr_skill_unknown(tmp_path: Path):
    """AC-SKILLS-003: FR-003 — an unknown skill name returns None."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillQuery
    from modules.skills.src.capabilities_skills_index_builder import (
    SkillsPackReader,
)

    pack = _make_pack(tmp_path)
    content = SkillsPackReader(pack).show_skill(SkillQuery("nope-missing"))
    assert content is None