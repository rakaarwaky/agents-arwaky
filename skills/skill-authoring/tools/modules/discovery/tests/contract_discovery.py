"""Contract tests: discovery capability impls implement their contract ABCs.

Proves each protocol impl exists and is a proper instance of the
contract, so a missing or renamed implementor fails the suite.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Bootstrap sys.path so `discovery.*` and `shared.src.*` resolve as
# top-level packages (mirrors modules/conftest.py path setup).
_MOD_ROOT = Path(__file__).resolve().parent.parent.parent
for _ns in (_MOD_ROOT,):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))

from discovery.agent_discovery_orchestrator import SkillsDiscoveryAgent
from discovery.capabilities_discovery_catalog import SkillsCatalog
from discovery.capabilities_discovery_finder import (
    SkillsBm25fRanker,
    SkillsDiscover,
)
from discovery.capabilities_discovery_lister import SkillsLister
from discovery.capabilities_discovery_reader import SkillsPackReader
from shared.src.discovery.contract_discovery_protocol import (
    ISkillsCatalogProtocol,
    ISkillsDiscoverProtocol,
    ISkillsListerProtocol,
    ISkillsReaderProtocol,
)
from discovery.contract_discovery_aggregate import ISkillsDiscoveryAggregate


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
