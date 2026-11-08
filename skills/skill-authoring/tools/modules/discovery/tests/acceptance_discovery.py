"""Acceptance tests: business requirements the discovery feature must meet."""
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
from shared.src.design.taxonomy_skills_response import SkillsExitCode  # type: ignore[assignment]


def _agent(root: Path) -> SkillsDiscoveryAgent:
    catalog = SkillsCatalog()
    return SkillsDiscoveryAgent(
        catalog=catalog,
        discover=SkillsDiscover(catalog, SkillsBm25fRanker()),
        lister=SkillsLister(root),
        reader=SkillsPackReader(root),
    )


def test_drift_fails_closed(tmp_path):
    """ACC-DISCOVERY-001: a stale catalog must not silently answer discover."""
    cat_dir = tmp_path / "automation" / "fetch"
    cat_dir.mkdir(parents=True)
    (cat_dir / "SKILL.md").write_text(
        "---\nname: fetch\ndescription: A fetch skill.\n---\n# Fetch\n",
        encoding="utf-8",
    )
    catalog = SkillsCatalog()
    report = catalog.rebuild(DiscoveryRoot(tmp_path))
    assert report.skills == 1

    # Drift the tracked artifact: add a skill the catalog does not know.
    new_dir = tmp_path / "automation" / "brand-new"
    new_dir.mkdir(parents=True)
    (new_dir / "SKILL.md").write_text(
        "---\nname: brand-new\ndescription: A newer skill.\n---\n# New\n",
        encoding="utf-8",
    )
    check = catalog.check(DiscoveryRoot(tmp_path))
    assert check.in_sync is False
    # The agent maps a drift check to exit 3 (drift category per contract).
    result = _agent(tmp_path).execute(
        DiscoveryRequest(
            verb=DiscoveryVerb.CATALOG,
            root=DiscoveryRoot(tmp_path),
            flags={"check": True},
        )
    )
    assert result.ok is False
    assert result.exit_code != SkillsExitCode.CLEAN


def test_unknown_op_maps_to_usage_error(tmp_path):
    """ACC-DISCOVERY-002: an unknown verb returns a usage-error result."""
    result = _agent(tmp_path).execute(
        DiscoveryRequest(
            verb="bogus-verb",
            root=DiscoveryRoot(tmp_path),
        )
    )
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.USAGE_ERROR
