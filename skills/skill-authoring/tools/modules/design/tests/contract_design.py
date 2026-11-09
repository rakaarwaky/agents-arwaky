"""Design-module contract test (AES704).

Verifies that SkillsDesignAgent implements ISkillsDesignAggregate.
"""

from __future__ import annotations

from design.src.agent_design_orchestrator import SkillsDesignAgent
from shared.src.design.contract_design_aggregate import ISkillsDesignAggregate


def test_agent_implements_protocol() -> None:
    agent = SkillsDesignAgent()
    assert isinstance(agent, ISkillsDesignAggregate)
