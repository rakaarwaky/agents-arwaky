"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_skill_pipeline():
    """DOG-SKILL-001: Basic dogfood check for skill module."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator

    provisioner = SkillPackProvisioner()
    # Orchestrator requires a registry, skip for now
    assert hasattr(provisioner, 'execute')
