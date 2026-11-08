"""Integration tests: DI wiring of the discovery agent over real pack trees."""
from __future__ import annotations

import sys
from pathlib import Path

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
from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.design.taxonomy_skills_response import SkillsExitCode


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
    result = agent.execute(SkillsRequest(op=SkillsOp.LIST, root=SkillsRoot(tmp_path)))
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
        SkillsRequest(
            op=SkillsOp.READ, query=SkillQuery("fetch"), root=SkillsRoot(tmp_path),
        )
    )
    assert result.ok is True
    assert "Fetch web content" in str(result.content)
