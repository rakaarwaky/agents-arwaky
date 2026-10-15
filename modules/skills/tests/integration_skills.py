"""Integration tests for modules/skills — layers wired together."""
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


def test_container_wires_agent_to_capability(tmp_path: Path):
    """INT-SKILLS-001: the container wires the capability into the agent."""
    from modules.shared.src.skills.taxonomy_skills_vo import SkillsRequest
    from modules.skills.src.capabilities_skills_index_builder import SkillsIndexBuilder
    from modules.skills.src.root_skills_container import default_aggregate

    aggregate = default_aggregate(index=SkillsIndexBuilder(_make_pack(tmp_path)))
    result = aggregate.execute(SkillsRequest(op="list"))
    assert result.ok
    assert [r.name for r in result.records] == ["fetch-mcp"]


def test_surface_through_container(tmp_path: Path):
    """INT-SKILLS-002: surface + container resolve a show request."""
    from modules.cli.src.surface_skills_command import cmd_skills
    from modules.skills.src.capabilities_skills_index_builder import SkillsIndexBuilder
    from modules.skills.src.root_skills_container import default_aggregate

    aggregate = default_aggregate(index=SkillsIndexBuilder(_make_pack(tmp_path)))
    rc = cmd_skills(["show", "fetch-mcp"], aggregate)
    assert rc == 0
