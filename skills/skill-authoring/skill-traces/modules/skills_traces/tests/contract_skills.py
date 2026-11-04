"""Contract tests for the shared skills contract (skills_design + skills_traces)."""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from skills_design.src.agent_skills_orchestrator import SkillsAgent
from skills_design.src.capabilities_skills_archiver import SkillsArchiver
from skills_design.src.capabilities_skills_catalog import SkillsCatalog
from skills_design.src.capabilities_skills_creator import SkillsCreator
from skills_design.src.capabilities_skills_discover import SkillsDiscover
from skills_design.src.capabilities_skills_linter import SkillsLinter
from skills_design.src.capabilities_skills_lister import SkillsLister
from skills_design.src.capabilities_skills_mover import SkillsMover
from skills_design.src.capabilities_skills_reader import SkillsPackReader

from skills_traces.src.contract_skills_aggregate import ISkillsAggregate
from skills_traces.src.contract_skills_protocol import (
    ISkillsArchiverProtocol,
    ISkillsCatalogProtocol,
    ISkillsCreatorProtocol,
    ISkillsDiscoverProtocol,
    ISkillsLinterProtocol,
    ISkillsListerProtocol,
    ISkillsMoverProtocol,
    ISkillsReaderProtocol,
    ISkillsTracesProtocol,
)
from skills_traces.src.capabilities_skills_traces import SkillsTraces


def test_lister_protocol_exists() -> None:
    """CP-SKILLS-001: ISkillsListerProtocol is an abstract contract with the lister seam."""
    assert "list_skills" in ISkillsListerProtocol.__abstractmethods__


def test_skills_aggregate_exists() -> None:
    """CP-SKILLS-002: ISkillsAggregate is an abstract contract with the execute seam."""
    assert "execute" in ISkillsAggregate.__abstractmethods__


def test_lister_implements_protocol(tmp_path: Path) -> None:
    """CP-SKILLS-003: SkillsLister implements ISkillsListerProtocol."""
    lister = SkillsLister(tmp_path)
    assert isinstance(lister, ISkillsListerProtocol)


def test_agent_implements_aggregate(tmp_path: Path) -> None:
    """CP-SKILLS-004: SkillsAgent implements ISkillsAggregate."""
    agent = SkillsAgent(SkillsLister(tmp_path), SkillsPackReader(tmp_path))
    assert isinstance(agent, ISkillsAggregate)


def test_reader_implements_protocol(tmp_path: Path) -> None:
    """CP-SKILLS-005: SkillsPackReader implements ISkillsReaderProtocol."""
    reader = SkillsPackReader(tmp_path)
    assert isinstance(reader, ISkillsReaderProtocol)


def test_catalog_implements_protocol() -> None:
    """CP-SKILLS-007: SkillsCatalog implements ISkillsCatalogProtocol."""
    catalog = SkillsCatalog()
    assert isinstance(catalog, ISkillsCatalogProtocol)


def test_discover_implements_protocol() -> None:
    """CP-SKILLS-008: SkillsDiscover implements ISkillsDiscoverProtocol."""
    catalog: ISkillsCatalogProtocol = SkillsCatalog()
    discover = SkillsDiscover(catalog)
    assert isinstance(discover, ISkillsDiscoverProtocol)


@pytest.mark.parametrize(
    ("capability", "protocol"),
    [
        (SkillsLister, ISkillsListerProtocol),
        (SkillsPackReader, ISkillsReaderProtocol),
        (SkillsLinter, ISkillsLinterProtocol),
        (SkillsCatalog, ISkillsCatalogProtocol),
        (SkillsDiscover, ISkillsDiscoverProtocol),
        (SkillsMover, ISkillsMoverProtocol),
        (SkillsArchiver, ISkillsArchiverProtocol),
        (SkillsCreator, ISkillsCreatorProtocol),
        (SkillsAgent, ISkillsAggregate),
        (SkillsTraces, ISkillsTracesProtocol),
    ],
    ids=[
        "lister",
        "pack-reader",
        "linter",
        "catalog",
        "discover",
        "mover",
        "archiver",
        "creator",
        "agent",
        "traces",
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
