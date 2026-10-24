"""Contract tests for modules/skills — verify protocol implementations."""
from __future__ import annotations

from pathlib import Path


def test_skills_protocol_exists() -> None:
    """CP-SKILLS-001: ISkillsIndexProtocol exists and can be imported."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsIndexProtocol,
    )

    assert ISkillsIndexProtocol is not None


def test_skills_aggregate_exists() -> None:
    """CP-SKILLS-002: ISkillsAggregate exists and can be imported."""
    from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate

    assert ISkillsAggregate is not None


def test_index_builder_implements_protocol(tmp_path: Path) -> None:
    """CP-SKILLS-003: SkillsIndexBuilder implements ISkillsIndexProtocol."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsIndexProtocol,
    )
    from modules.skills.src.capabilities_skills_index_builder import (
        SkillsIndexBuilder,
    )

    builder = SkillsIndexBuilder(tmp_path)
    assert isinstance(builder, ISkillsIndexProtocol)


def test_agent_implements_aggregate(tmp_path: Path) -> None:
    """CP-SKILLS-004: SkillsAgent implements ISkillsAggregate."""
    from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
    from modules.skills.src.agent_skills_orchestrator import SkillsAgent
    from modules.skills.src.capabilities_skills_index_builder import (
        SkillsIndexBuilder,
    )
    from modules.skills.src.capabilities_skills_pack_reader import SkillsPackReader

    agent = SkillsAgent(SkillsIndexBuilder(tmp_path), SkillsPackReader(tmp_path))
    assert isinstance(agent, ISkillsAggregate)


def test_reader_implements_protocol(tmp_path: Path) -> None:
    """CP-SKILLS-005: SkillsPackReader implements ISkillsReaderProtocol."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsReaderProtocol,
    )
    from modules.skills.src.capabilities_skills_pack_reader import (
        SkillsPackReader,
    )

    reader = SkillsPackReader(tmp_path)
    assert isinstance(reader, ISkillsReaderProtocol)


def test_validator_implements_protocol() -> None:
    """CP-SKILLS-006: SkillsValidator implements ISkillsValidatorProtocol."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsValidatorProtocol,
    )
    from modules.skills.src.capabilities_skills_validator import (
        SkillsValidator,
    )

    validator = SkillsValidator()
    assert isinstance(validator, ISkillsValidatorProtocol)


def test_catalog_implements_protocol() -> None:
    """CP-SKILLS-007: SkillsCatalog implements ISkillsCatalogProtocol."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsCatalogProtocol,
    )
    from modules.skills.src.capabilities_skills_catalog import (
        SkillsCatalog,
    )

    catalog = SkillsCatalog()
    assert isinstance(catalog, ISkillsCatalogProtocol)


def test_discoverer_implements_protocol() -> None:
    """CP-SKILLS-008: SkillsDiscoverer implements ISkillsDiscovererProtocol."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsCatalogProtocol,
        ISkillsDiscovererProtocol,
    )
    from modules.skills.src.capabilities_skills_catalog import (
        SkillsCatalog,
    )
    from modules.skills.src.capabilities_skills_discoverer import (
        SkillsDiscoverer,
    )

    catalog: ISkillsCatalogProtocol = SkillsCatalog()
    discoverer = SkillsDiscoverer(catalog)
    assert isinstance(discoverer, ISkillsDiscovererProtocol)


def test_mutator_implements_protocol() -> None:
    """CP-SKILLS-009: SkillsMutator implements ISkillsMutatorProtocol."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsMutatorProtocol,
    )
    from modules.skills.src.capabilities_skills_mutator import (
        SkillsMutator,
    )

    mutator = SkillsMutator()
    assert isinstance(mutator, ISkillsMutatorProtocol)


def test_merge_planner_implements_protocol() -> None:
    """CP-SKILLS-010: SkillsMergePlanner implements ISkillsMergePlannerProtocol."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsMergePlannerProtocol,
    )
    from modules.skills.src.capabilities_skills_merge_planner import (
        SkillsMergePlanner,
    )

    planner = SkillsMergePlanner()
    assert isinstance(planner, ISkillsMergePlannerProtocol)


def test_rules_renderer_implements_protocol() -> None:
    """CP-SKILLS-011: SkillsRulesRenderer implements ISkillsRulesRendererProtocol."""
    from modules.shared.src.skills.contract_skills_protocol import (
        ISkillsRulesRendererProtocol,
    )
    from modules.skills.src.capabilities_skills_rules_renderer import (
        SkillsRulesRenderer,
    )

    renderer = SkillsRulesRenderer()
    assert isinstance(renderer, ISkillsRulesRendererProtocol)
