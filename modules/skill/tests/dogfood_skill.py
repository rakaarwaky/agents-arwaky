"""Dogfood tests — runs against live service/session."""
from __future__ import annotations

import pytest


@pytest.mark.dogfood
def test_dogfood_skill_pipeline():
    """DOG-SKILL-001: Basic dogfood check for skill module."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator

    provisioner = SkillPackProvisioner()
    assert not hasattr(provisioner, 'execute')
    for method in ("provision", "prune", "audit"):
        assert callable(getattr(provisioner, method))

    from modules.skill.src.surface_skill_command import SkillRegistryAdapter
    adapter = SkillRegistryAdapter()
    assert not hasattr(adapter, 'execute')
    for method in ("list", "check", "show", "install", "uninstall", "sync"):
        assert callable(getattr(adapter, method))
