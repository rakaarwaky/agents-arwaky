"""Unit tests for modules/governance — agent routing and capability helpers."""
from __future__ import annotations

from unittest.mock import MagicMock

from shared.src.design.taxonomy_skills_request import (
    SkillQuery,
    SkillsOp,
    SkillsRequest,
)
from shared.src.design.taxonomy_skills_response import SkillsExitCode


def _agent():
    from governance.agent_governance_orchestrator import SkillsGovernanceAgent

    locker = MagicMock()
    piner = MagicMock()
    mover = MagicMock()
    return SkillsGovernanceAgent(locker=locker, piner=piner, mover=mover), (
        locker,
        piner,
        mover,
    )


def test_agent_routes_pin_to_piner():
    """UT-GOVERNANCE-001: a PIN request reaches the piner, not the locker."""
    agent, (locker, piner, _mover) = _agent()
    req = SkillsRequest(op=SkillsOp.PIN, query=SkillQuery("skill-a"))
    agent.execute(req)
    assert piner.pin.called, "PIN must reach the piner"
    assert not locker.lock.called, "PIN must not touch the locker"


def test_agent_routes_lock_to_locker():
    """UT-GOVERNANCE-002: a LOCK request reaches the locker, not the piner."""
    agent, (locker, piner, _mover) = _agent()
    req = SkillsRequest(op=SkillsOp.LOCK, query=SkillQuery("skill-a"))
    agent.execute(req)
    assert locker.lock.called, "LOCK must reach the locker"
    assert not piner.pin.called, "LOCK must not touch the piner"


def test_agent_routes_move_to_mover():
    """UT-GOVERNANCE-003: a MOVE request reaches the mover."""
    agent, (_locker, _piner, mover) = _agent()
    req = SkillsRequest(
        op=SkillsOp.MOVE, query=SkillQuery("skill-a"), flags={"target": "cat"}
    )
    agent.execute(req)
    assert mover.plan_move.called, "MOVE must reach the mover"


def test_agent_unknown_op_returns_usage_error():
    """UT-GOVERNANCE-004: an unknown op name returns a usage error."""
    agent, _ = _agent()
    # The op is passed as the raw string name, matching how the surface
    # forwards an unvalidated flag.
    req = SkillsRequest(op="bogus-op")
    result = agent.execute(req)
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.USAGE_ERROR


def test_agent_missing_capability_raises():
    """UT-GOVERNANCE-005: dispatching to an unwired capability raises."""
    from shared.src.common.taxonomy_common_error import SkillsRootError

    from governance.agent_governance_orchestrator import SkillsGovernanceAgent

    agent = SkillsGovernanceAgent(locker=None, piner=None, mover=None)
    req = SkillsRequest(op=SkillsOp.PIN, query=SkillQuery("skill-a"))
    try:
        # Bypass execute()'s SkillsError catch so we can assert the
        # typed raise out of _mutate_skill / _require.
        agent._execute_pin(req, SkillsOp.PIN)
    except SkillsRootError:
        return
    raise AssertionError("expected SkillsRootError for an unwired capability")


def test_agent_show_skill_returns_usage_error():
    """UT-GOVERNANCE-006: show_skill returns a usage error, never NotImplementedError."""
    agent, _ = _agent()
    result = agent.show_skill("skill-a")
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.USAGE_ERROR
