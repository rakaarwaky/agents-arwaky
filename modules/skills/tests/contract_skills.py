"""Contract tests for modules/skills — verify protocol implementations."""
from __future__ import annotations

from pathlib import Path


def test_skills_protocol_exists():
    """CP-SKILLS-001: ISkillsIndexProtocol exists and can be imported."""
    from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsIndexProtocol,
)

    assert ISkillsIndexProtocol is not None


def test_skills_aggregate_exists():
    """CP-SKILLS-002: ISkillsAggregate exists and can be imported."""
    from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate

    assert ISkillsAggregate is not None


def test_index_builder_implements_protocol(tmp_path: Path):
    """CP-SKILLS-003: SkillsIndexBuilder implements ISkillsIndexProtocol."""
    from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsIndexProtocol,
)
    from modules.skills.src.capabilities_skills_index_builder import (
    SkillsIndexBuilder,
)

    builder = SkillsIndexBuilder(tmp_path)
    assert isinstance(builder, ISkillsIndexProtocol)


def test_agent_implements_aggregate(tmp_path: Path):
    """CP-SKILLS-004: SkillsAgent implements ISkillsAggregate."""
    from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
    from modules.skills.src.agent_skills_orchestrator import SkillsAgent
    from modules.skills.src.capabilities_skills_index_builder import (
    SkillsIndexBuilder,
    SkillsPackReader,
)

    agent = SkillsAgent(SkillsIndexBuilder(tmp_path), SkillsPackReader(tmp_path))
    assert isinstance(agent, ISkillsAggregate)