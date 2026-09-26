"""Integration tests for modules/skill — real wiring and end-to-end paths."""
from __future__ import annotations

import tempfile
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

    from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest, ToolFilter

    aggregate = create_skill_feature()
    with tempfile.TemporaryDirectory() as tmp:
        result = aggregate.execute(
            SkillRequest(
                SkillOp("provision"),
                tool_filter=ToolFilter("lint"),
                target=Path(tmp),
                force=True,
            )
        )
    assert result.result == 0


def test_orchestrator_execute_audit():
    """IT-SKILL-004: Audit flow executes and returns findings."""
    from modules.skill.src.root_skill_container import create_skill_feature

    from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

    aggregate = create_skill_feature()
    result = aggregate.execute(SkillRequest(SkillOp("audit")))
    assert result.result in (0, 1)


def test_orchestrator_list():
    """IT-SKILL-005: list() returns exit code."""
    from modules.skill.src.root_skill_container import create_skill_feature

    from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

    aggregate = create_skill_feature()
    result = aggregate.execute(SkillRequest(SkillOp("list")))
    assert result.result == 0


def test_orchestrator_check():
    """IT-SKILL-006: check() returns exit code."""
    from modules.skill.src.root_skill_container import create_skill_feature

    from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest

    aggregate = create_skill_feature()
    result = aggregate.execute(SkillRequest(SkillOp("check")))
    assert result.result in (0, 1)


def test_orchestrator_show():
    """IT-SKILL-007: show() returns exit code for missing skill."""
    from modules.skill.src.root_skill_container import create_skill_feature

    from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest, SkillQuery

    aggregate = create_skill_feature()
    result = aggregate.execute(
        SkillRequest(SkillOp("show"), query=SkillQuery("nonexistent-skill-12345"))
    )
    assert result.result != 0


def test_orchestrator_uninstall():
    """IT-SKILL-008: execute(uninstall) returns an exit code."""
    from modules.skill.src.root_skill_container import create_skill_feature
    from modules.shared.src.taxonomy_skill_vo import SkillArgs, SkillOp, SkillRequest

    aggregate = create_skill_feature()
    result = aggregate.execute(SkillRequest(SkillOp("uninstall"), args=SkillArgs(["nonexistent"])))
    assert result.result != 0


def test_orchestrator_sync():
    """IT-SKILL-009: execute(sync) returns an exit code."""
    from modules.skill.src.root_skill_container import create_skill_feature
    from modules.shared.src.taxonomy_skill_vo import SkillArgs, SkillOp, SkillRequest

    aggregate = create_skill_feature()
    result = aggregate.execute(SkillRequest(SkillOp("sync"), args=SkillArgs([])))
    assert result.result in (0, 1)


def test_pack_provisioner_audits_real_pack():
    """IT-SKILL-010: SkillPackProvisioner.audit returns list of findings."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    findings = provisioner.audit()
    assert isinstance(findings, list)


def test_registry_adapter_rich_methods():
    """IT-SKILL-011: SkillRegistryAdapter exposes the rich protocol methods."""
    from modules.shared.src.contract_skill_protocol import ISkillRegistryProtocol
    from modules.skill.src.surface_skill_command import SkillRegistryAdapter
    from modules.shared.src.taxonomy_skill_vo import SkillArgs, SkillQuery

    adapter = SkillRegistryAdapter()
    assert isinstance(adapter, ISkillRegistryProtocol)
    assert not hasattr(adapter, "execute")

    assert adapter.list() is not None
    assert adapter.check() is not None
    assert adapter.show(SkillQuery("lint-arwaky")) is not None
    assert adapter.sync(SkillArgs([])) is not None