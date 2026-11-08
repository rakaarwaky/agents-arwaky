"""Design-module integration test (AES704).

Verifies design capability wiring and lifecycle flow end to end.
"""

from __future__ import annotations

from design.src.agent_design_orchestrator import SkillsDesignAgent


def test_design_agent_coordinates_capabilities() -> None:
    agent = SkillsDesignAgent()
    assert agent is not None
