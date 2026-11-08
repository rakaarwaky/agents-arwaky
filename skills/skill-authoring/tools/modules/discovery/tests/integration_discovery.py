"""Integration tests: DI wiring of the discovery agent over real pack trees."""
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
from shared.src.discovery.taxonomy_discovery_request import (
    DiscoveryQuery,
    DiscoveryRequest,
    DiscoveryRoot,
    DiscoveryVerb,
)
from shared.src.discovery.taxonomy_discovery_vo import SkillsBm25fRanker


def _make_agent(root: Path) -> SkillsDiscoveryAgent:
    catalog = SkillsCatalog()
    discover = SkillsDiscover(catalog, SkillsBm25fRanker())
    lister = SkillsLister(root)
    reader = SkillsPackReader(root)
    return SkillsDiscoveryAgent(
        catalog=catalog, discover=discover, lister=lister, reader=reader,
    )


def test_list_routes_to_lister(tmp_path):
    """INT-DISCOVERY-001: LIST op resolves through the injected lister."""
    skill = tmp_path / "automation" / "fetch" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: fetch\ndescription: Fetch web content.\n---\n# Fetch\n",
        encoding="utf-8",
    )
    agent = _make_agent(tmp_path)
    result = agent.execute(
        DiscoveryRequest(verb=DiscoveryVerb.LIST, root=DiscoveryRoot(tmp_path))
    )
    assert result.ok is True
    assert len(result.records) == 1
    assert result.records[0].name == "fetch"


def test_read_routes_to_reader(tmp_path):
    """INT-DISCOVERY-002: READ op resolves one skill through the reader."""
    skill = tmp_path / "automation" / "fetch" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: fetch\ndescription: Fetch web content.\n---\n# Fetch\n",
        encoding="utf-8",
    )
    agent = _make_agent(tmp_path)
    result = agent.execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.READ,
            query=DiscoveryQuery("fetch"),
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert result.ok is True
    assert "Fetch web content" in str(result.content)
