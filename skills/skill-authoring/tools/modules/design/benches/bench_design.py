"""Design-module benchmark (AES704).

Performance regression benchmark for the design agent's op dispatch path.
"""

from __future__ import annotations

from design.src.agent_design_orchestrator import SkillsDesignAgent
from shared.src.design.taxonomy_skills_request import SkillsOp, SkillsRequest
from shared.src.design.taxonomy_skills_response import SkillsResult


def bench_design_dispatch() -> None:
    """Time op dispatch through the design agent."""
    agent = SkillsDesignAgent()
    _ = agent.execute(SkillsRequest(op=SkillsOp.LINT, query=""))
    _ = agent.execute(SkillsRequest(op=SkillsOp.RUN, query=""))
    _ = agent.execute(SkillsRequest(op=SkillsOp.PAUSE, query=""))
