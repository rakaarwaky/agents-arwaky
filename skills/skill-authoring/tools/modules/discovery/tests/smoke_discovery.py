"""Smoke test: the discovery agent boots and routes an op end to end."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TOOLS_ROOT = Path(__file__).resolve().parents[2]
for _ns in (
    _TOOLS_ROOT,
    _TOOLS_ROOT / "shared" / "src",
    _TOOLS_ROOT / "discovery" / "src",
):
    if _ns.is_dir() and str(_ns) not in sys.path:
        sys.path.insert(0, str(_ns))

from agent_discovery_orchestrator import SkillsDiscoveryAgent
from capabilities_discovery_catalog import SkillsCatalog
from capabilities_discovery_finder import SkillsDiscover
from capabilities_discovery_lister import SkillsLister
from capabilities_discovery_reader import SkillsPackReader
from shared.src.discovery.taxonomy_discovery_vo import SkillsBm25fRanker
from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryRequest,
    DiscoveryRoot,
    DiscoveryVerb,
)


def test_agent_boots_and_routes(tmp_path):
    """SMOKE-DISCOVERY-001: agent constructs and returns a typed result."""
    skill = tmp_path / "automation" / "fetch" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: fetch\ndescription: Fetch web content.\n---\n# Fetch\n",
        encoding="utf-8",
    )
    catalog = SkillsCatalog()
    agent = SkillsDiscoveryAgent(
        catalog=catalog,
        discover=SkillsDiscover(catalog, SkillsBm25fRanker()),
        lister=SkillsLister(tmp_path),
        reader=SkillsPackReader(tmp_path),
    )
    result = agent.execute(
        DiscoveryRequest(verb=DiscoveryVerb.LIST, root=DiscoveryRoot(tmp_path))
    )
    assert result.ok is True
    assert result.verb == DiscoveryVerb.LIST
