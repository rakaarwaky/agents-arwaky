"""Smoke tests for modules/skill — fast boot and import checks."""
from __future__ import annotations

import time


def test_import_skill_module():
    """SM-SKILL-001: modules.skill can be imported."""
    import modules.skill
    assert modules.skill is not None


def test_import_skill_src():
    """SM-SKILL-002: modules.skill.src can be imported."""
    from modules.skill import src
    assert src is not None


def test_import_skill_pack_capability():
    """SM-SKILL-003: capabilities_skill_pack imports cleanly."""
    from modules.skill.src import capabilities_skill_pack
    assert capabilities_skill_pack is not None


def test_import_skill_orchestrator():
    """SM-SKILL-004: agent_skill_orchestrator imports cleanly."""
    from modules.skill.src import agent_skill_orchestrator
    assert agent_skill_orchestrator is not None


def test_import_skill_surface():
    """SM-SKILL-005: surface_skill_command imports cleanly."""
    from modules.skill.src import surface_skill_command
    assert surface_skill_command is not None


def test_import_skill_container():
    """SM-SKILL-006: root_skill_container imports cleanly."""
    from modules.skill.src import root_skill_container
    assert root_skill_container is not None


def test_import_skill_pack_provisioner():
    """SM-SKILL-007: SkillPackProvisioner can be imported."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner
    assert SkillPackProvisioner is not None


def test_import_skill_orchestrator_class():
    """SM-SKILL-008: SkillOrchestrator can be imported."""
    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
    assert SkillOrchestrator is not None


def test_import_skill_registry_adapter():
    """SM-SKILL-009: SkillRegistryAdapter can be imported."""
    from modules.skill.src.surface_skill_command import SkillRegistryAdapter
    assert SkillRegistryAdapter is not None


def test_import_skill_container_class():
    """SM-SKILL-010: SkillContainer can be imported."""
    from modules.skill.src.root_skill_container import SkillContainer
    assert SkillContainer is not None


def test_import_create_skill_feature():
    """SM-SKILL-011: create_skill_feature can be imported."""
    from modules.skill.src.root_skill_container import create_skill_feature
    assert callable(create_skill_feature)


def test_init_quickly():
    """SM-SKILL-012: SkillPackProvisioner init completes quickly."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    start = time.time()
    provisioner = SkillPackProvisioner()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Init took {elapsed:.2f}s"
    assert provisioner is not None


def test_container_creation_quickly():
    """SM-SKILL-013: SkillContainer creation completes quickly."""
    from modules.skill.src.root_skill_container import SkillContainer

    start = time.time()
    container = SkillContainer()
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Container init took {elapsed:.2f}s"
    assert container.aggregate is not None
