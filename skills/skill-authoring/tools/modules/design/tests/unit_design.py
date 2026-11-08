"""Design-module unit test (AES704).

Verifies the agent's op-handler dispatch and error propagation.
"""

from __future__ import annotations

from design.src.agent_design_orchestrator import SkillsDesignAgent
from shared.src.design.taxonomy_skills_request import SkillsOp, SkillsRequest
from shared.src.design.taxonomy_skills_response import SkillsExitCode


def test_unknown_op_returns_usage_error() -> None:
    agent = SkillsDesignAgent()
    result = agent.execute(SkillsRequest(op=SkillsOp("bogus"), query=""))
    assert result.ok is False
    assert result.exit_code == SkillsExitCode.USAGE_ERROR
