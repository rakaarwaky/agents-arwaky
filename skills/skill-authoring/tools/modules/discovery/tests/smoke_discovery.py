"""Smoke test: the discovery agent boots and routes an op end to end."""
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
    SkillsOp,
    SkillsRequest,
    SkillsRoot,
)
from shared.src.design.taxonomy_skills_response import SkillsExitCode


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
        SkillsRequest(op=SkillsOp.LIST, root=SkillsRoot(tmp_path))
    )
    assert result.ok is True
    assert result.op == SkillsOp.LIST
