"""Smoke tests for modules/governance — fast import and construction checks."""
from __future__ import annotations


def test_import_governance_module():
    """SM-GOVERNANCE-001: the governance module can be imported."""
    import governance
    assert governance is not None


def test_import_governance_agent():
    """SM-GOVERNANCE-002: the governance agent can be imported."""
    from governance.agent_governance_orchestrator import (
        SkillsGovernanceAgent,
    )
    assert SkillsGovernanceAgent is not None


def test_import_governance_capabilities():
    """SM-GOVERNANCE-003: the three governance capabilities can be imported."""
    from governance.capabilities_skills_locker import SkillsLocker
    from governance.capabilities_skills_mover import SkillsMover
    from governance.capabilities_skills_piner import SkillsPiner

    for cap in (SkillsLocker(), SkillsMover(), SkillsPiner()):
        assert cap is not None


def test_agent_constructs_with_none_capabilities():
    """SM-GOVERNANCE-004: the agent constructs with an all-None wiring."""
    from governance.agent_governance_orchestrator import SkillsGovernanceAgent

    agent = SkillsGovernanceAgent(locker=None, piner=None, mover=None)
    assert agent is not None
