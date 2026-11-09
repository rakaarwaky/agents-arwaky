"""Design-module acceptance test (AES704).

Acceptance-level check for design agent readiness.
."""

from __future__ import annotations

from design.src.agent_design_orchestrator import SkillsDesignAgent


def test_design_acceptance_ready() -> None:
    agent = SkillsDesignAgent()
    assert agent is not None
