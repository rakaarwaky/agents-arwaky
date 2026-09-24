"""Integration tests for modules/skill — real wiring and end-to-end paths."""
from __future__ import annotations

from pathlib import Path


def test_skill_container_wires_correctly():
    """IT-SKILL-001: SkillContainer creates valid orchestrator."""
    from modules.skill.src.root_skill_container import SkillContainer

    container = SkillContainer()
    aggregate = container.aggregate
    assert aggregate is not None


def test_create_skill_feature_returns_valid():
    """IT-SKILL-002: create_skill_feature returns usable aggregate."""
    from modules.skill.src.root_skill_container import create_skill_feature

    aggregate = create_skill_feature()
    assert aggregate is not None


def test_orchestrator_execute_provision():
    """IT-SKILL-003: Full provision flow executes without error."""
    from modules.skill.src.root_skill_container import create_skill_feature

    aggregate = create_skill_feature()
    result = aggregate.execute("provision", "lint")
    assert isinstance(result, int)


def test_orchestrator_execute_audit():
    """IT-SKILL-004: Audit flow executes and returns findings."""
    from modules.skill.src.root_skill_container import create_skill_feature

    aggregate = create_skill_feature()
    result = aggregate.execute("audit")
    assert isinstance(result, int)


def test_orchestrator_list():
    """IT-SKILL-005: list() returns exit code."""
    from modules.skill.src.root_skill_container import create_skill_feature

    aggregate = create_skill_feature()
    result = aggregate.list()
    assert isinstance(result, int)


def test_orchestrator_check():
    """IT-SKILL-006: check() returns exit code."""
    from modules.skill.src.root_skill_container import create_skill_feature

    aggregate = create_skill_feature()
    result = aggregate.check()
    assert isinstance(result, int)


def test_orchestrator_show():
    """IT-SKILL-007: show() returns exit code for missing skill."""
    from modules.skill.src.root_skill_container import create_skill_feature

    aggregate = create_skill_feature()
    result = aggregate.show("nonexistent-skill-12345")
    assert isinstance(result, int)


def test_orchestrator_uninstall():
    """IT-SKILL-008: uninstall() returns exit code."""
    from modules.skill.src.root_skill_container import create_skill_feature
    from modules.shared.src.taxonomy_skill_vo import SkillArgs

    aggregate = create_skill_feature()
    result = aggregate.uninstall(SkillArgs(["nonexistent"]))
    assert isinstance(result, int)


def test_orchestrator_sync():
    """IT-SKILL-009: sync() returns exit code."""
    from modules.skill.src.root_skill_container import create_skill_feature
    from modules.shared.src.taxonomy_skill_vo import SkillArgs

    aggregate = create_skill_feature()
    result = aggregate.sync(SkillArgs([]))
    assert isinstance(result, int)


def test_pack_provisioner_audits_real_pack():
    """IT-SKILL-010: SkillPackProvisioner.audit returns list of findings."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    findings = provisioner.audit()
    assert isinstance(findings, list)


def test_registry_adapter_execute_variants():
    """IT-SKILL-011: SkillRegistryAdapter handles all op variants."""
    from modules.skill.src.surface_skill_command import SkillRegistryAdapter

    adapter = SkillRegistryAdapter()

    # These should not raise
    _ = adapter.execute("list")
    _ = adapter.execute("check")
    _ = adapter.execute("show", "lint")
    _ = adapter.execute("install", "lint")
    _ = adapter.execute("uninstall", "lint")
    _ = adapter.execute("sync")