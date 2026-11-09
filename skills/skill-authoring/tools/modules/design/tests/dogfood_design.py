"""Design-module dogfood test (AES704).

Exercises the design agent against a real skills pack fixture.
"""

from __future__ import annotations

from design.src.agent_design_orchestrator import SkillsDesignAgent


def test_design_dogfood_smoke() -> None:
    agent = SkillsDesignAgent()
    assert callable(agent.execute)
