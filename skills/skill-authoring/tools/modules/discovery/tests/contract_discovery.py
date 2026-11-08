"""Contract tests: discovery capability impls implement their contract ABCs.

Proves each protocol impl exists and is a proper instance of the
contract, so a missing or renamed implementor fails the suite.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Bootstrap sys.path so `shared.src.*`, `discovery.contract_*`, and the
# `discovery/src` capability modules resolve (mirrors modules/conftest.py).
_TOOLS_ROOT = Path(__file__).resolve().parents[2]
for _ns in (
    _TOOLS_ROOT,
    _TOOLS_ROOT / "shared" / "src",
    _TOOLS_ROOT / "discovery" / "src",
):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))

from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from shared.src.discovery.taxonomy_discovery_vo import SkillsBm25fRanker
from discovery.contract_discovery_aggregate import ISkillsDiscoveryAggregate
from agent_discovery_orchestrator import SkillsDiscoveryAgent
from capabilities_discovery_catalog import SkillsCatalog
from capabilities_discovery_finder import SkillsDiscover
from capabilities_discovery_lister import SkillsLister
from capabilities_discovery_reader import SkillsPackReader


def test_lister_implements_lister_protocol():
    """ISkillsListerProtocol is implemented by SkillsLister."""
    assert isinstance(SkillsLister(), ISkillsListerProtocol)


def test_reader_implements_reader_protocol():
    """ISkillsReaderProtocol is implemented by SkillsPackReader."""
    assert isinstance(SkillsPackReader(), ISkillsReaderProtocol)


def test_catalog_implements_catalog_protocol():
    """ISkillsCatalogProtocol is implemented by SkillsCatalog."""
    assert isinstance(SkillsCatalog(), ISkillsCatalogProtocol)


def test_discover_implements_discover_protocol():
    """ISkillsDiscoverProtocol is implemented by SkillsDiscover."""
    cap = SkillsCatalog()
    disc = SkillsDiscover(cap, SkillsBm25fRanker())
    assert isinstance(disc, ISkillsDiscoverProtocol)


def test_agent_implements_discovery_aggregate():
    """ISkillsDiscoveryAggregate is implemented by SkillsDiscoveryAgent."""
    cat = SkillsCatalog()
    disc = SkillsDiscover(cat, SkillsBm25fRanker())
    agent = SkillsDiscoveryAgent(
        catalog=cat, discover=disc,
        lister=SkillsLister(), reader=SkillsPackReader(),
    )
    assert isinstance(agent, ISkillsDiscoveryAggregate)
