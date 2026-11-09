"""Design-module smoke test (AES704).

Smoke-checks the design agent's public surface.
"""

from __future__ import annotations

from design.src.agent_design_orchestrator import SkillsDesignAgent


def test_design_smoke_surface() -> None:
    agent = SkillsDesignAgent()
    assert callable(agent.execute)
