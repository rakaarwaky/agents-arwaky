"""Contract tests for modules/skills — verify protocol implementations."""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from modules.shared.src.skills.contract_skills_aggregate import ISkillsAggregate
from modules.shared.src.skills.contract_skills_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscovererProtocol,
    ISkillsIndexProtocol,
    ISkillsMergePlannerProtocol,
    ISkillsMutatorProtocol,
    ISkillsReaderProtocol,
    ISkillsValidatorProtocol,
)
from modules.skills.src.agent_skills_orchestrator import SkillsAgent
from modules.skills.src.capabilities_skills_catalog import SkillsCatalog
from modules.skills.src.capabilities_skills_discoverer import SkillsDiscoverer
from modules.skills.src.capabilities_skills_index_builder import SkillsIndexBuilder
from modules.skills.src.capabilities_skills_merge_planner import SkillsMergePlanner
from modules.skills.src.capabilities_skills_mutator import SkillsMutator
from modules.skills.src.capabilities_skills_pack_reader import SkillsPackReader
from modules.skills.src.capabilities_skills_validator import SkillsValidator


def test_skills_protocol_exists() -> None:
    """CP-SKILLS-001: ISkillsIndexProtocol is an abstract contract with the index seam."""
    assert "list_skills" in ISkillsIndexProtocol.__abstractmethods__


def test_skills_aggregate_exists() -> None:
    """CP-SKILLS-002: ISkillsAggregate is an abstract contract with the execute seam."""
    assert "execute" in ISkillsAggregate.__abstractmethods__


def test_index_builder_implements_protocol(tmp_path: Path) -> None:
    """CP-SKILLS-003: SkillsIndexBuilder implements ISkillsIndexProtocol."""
    builder = SkillsIndexBuilder(tmp_path)
    assert isinstance(builder, ISkillsIndexProtocol)


def test_agent_implements_aggregate(tmp_path: Path) -> None:
    """CP-SKILLS-004: SkillsAgent implements ISkillsAggregate."""
    agent = SkillsAgent(SkillsIndexBuilder(tmp_path), SkillsPackReader(tmp_path))
    assert isinstance(agent, ISkillsAggregate)


def test_reader_implements_protocol(tmp_path: Path) -> None:
    """CP-SKILLS-005: SkillsPackReader implements ISkillsReaderProtocol."""
    reader = SkillsPackReader(tmp_path)
    assert isinstance(reader, ISkillsReaderProtocol)


def test_validator_implements_protocol() -> None:
    """CP-SKILLS-006: SkillsValidator implements ISkillsValidatorProtocol."""
    validator = SkillsValidator()
    assert isinstance(validator, ISkillsValidatorProtocol)


def test_catalog_implements_protocol() -> None:
    """CP-SKILLS-007: SkillsCatalog implements ISkillsCatalogProtocol."""
    catalog = SkillsCatalog()
    assert isinstance(catalog, ISkillsCatalogProtocol)


def test_discoverer_implements_protocol() -> None:
    """CP-SKILLS-008: SkillsDiscoverer implements ISkillsDiscovererProtocol."""
    catalog: ISkillsCatalogProtocol = SkillsCatalog()
    discoverer = SkillsDiscoverer(catalog)
    assert isinstance(discoverer, ISkillsDiscovererProtocol)


def test_mutator_implements_protocol() -> None:
    """CP-SKILLS-009: SkillsMutator implements ISkillsMutatorProtocol."""
    mutator = SkillsMutator()
    assert isinstance(mutator, ISkillsMutatorProtocol)


def test_merge_planner_implements_protocol() -> None:
    """CP-SKILLS-010: SkillsMergePlanner implements ISkillsMergePlannerProtocol."""
    planner = SkillsMergePlanner()
    assert isinstance(planner, ISkillsMergePlannerProtocol)


@pytest.mark.parametrize(
    ("capability", "protocol"),
    [
        (SkillsIndexBuilder, ISkillsIndexProtocol),
        (SkillsPackReader, ISkillsReaderProtocol),
        (SkillsValidator, ISkillsValidatorProtocol),
        (SkillsCatalog, ISkillsCatalogProtocol),
        (SkillsDiscoverer, ISkillsDiscovererProtocol),
        (SkillsMutator, ISkillsMutatorProtocol),
        (SkillsMergePlanner, ISkillsMergePlannerProtocol),
        (SkillsAgent, ISkillsAggregate),
    ],
    ids=[
        "index-builder",
        "pack-reader",
        "validator",
        "catalog",
        "discoverer",
        "mutator",
        "merge-planner",
        "agent",
    ],
)
def test_capability_signatures_compatible(
    capability: type, protocol: type
) -> None:
    """Each concrete class resolves every protocol abstract method, signature-compatible.

    A capability that drops or renames a protocol method would carry the
    name in ``__abstractmethods__`` and fail here with a named error. For
    every abstract method, the concrete class must expose a callable whose
    parameter names, kinds, defaults, and annotations match the protocol's.
    """
    assert not capability.__abstractmethods__, (
        f"{capability.__name__} leaves protocol methods unimplemented: "
        f"{sorted(capability.__abstractmethods__)}"
    )
    for name in protocol.__abstractmethods__:
        concrete = getattr(capability, name)
        abstract = getattr(protocol, name)
        assert callable(concrete), (
            f"{capability.__name__}.{name} is not callable"
        )
        concrete_sig = inspect.signature(concrete)
        protocol_sig = inspect.signature(abstract)
        assert concrete_sig.parameters == protocol_sig.parameters, (
            f"{capability.__name__}.{name}{concrete_sig} diverges from "
            f"{protocol.__name__}.{name}{protocol_sig}"
        )
