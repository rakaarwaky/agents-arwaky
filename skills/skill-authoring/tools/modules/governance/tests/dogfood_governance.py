"""Dogfood tests for modules/governance — the governance feature as a
real consumer of the shared kernel, run against the live skill pack.

Exercises the governance agent the way the CLI surface drives it: build a
typed request and let the agent route it to a live capability.
"""
from __future__ import annotations

from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)


def test_dogfood_agent_builds_requests_the_surface_way():
    """DOG-GOVERNANCE-001: the agent consumes a typed request end to end."""
    from governance.agent_governance_orchestrator import SkillsGovernanceAgent
    from governance.capabilities_skills_locker import SkillsLocker
    from governance.capabilities_skills_mover import SkillsMover
    from governance.capabilities_skills_piner import SkillsPiner

    agent = SkillsGovernanceAgent(
        locker=SkillsLocker(),
        piner=SkillsPiner(),
        mover=SkillsMover(),
    )
    # No root bound and an unknown skill name: the agent degrades to a
    # typed failure result rather than raising, which is the surface
    # contract the CLI relies on.
    result = agent.execute(
        SkillsRequest(op=SkillsOp.PIN, query=SkillQuery("no-such-skill"))
    )
    assert result.ok is False
