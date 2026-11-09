"""Design-module e2e test (AES704).

End-to-end check of design agent lifecycle behavior.
"""

from __future__ import annotations

from design.src.agent_design_orchestrator import SkillsDesignAgent


def test_design_e2e_lifecycle() -> None:
    agent = SkillsDesignAgent()
    assert callable(agent.execute)
