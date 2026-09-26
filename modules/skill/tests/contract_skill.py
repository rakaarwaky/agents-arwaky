"""Contract tests for modules/skill — prove protocol/interface implementations exist."""
from __future__ import annotations

from modules.shared.src.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.contract_skill_protocol import (
    ISkillProvisionProtocol,
    ISkillRegistryProtocol,
)


def test_skill_provision_protocol_exists():
    """CP-SKILL-001: ISkillProvisionProtocol is an ABC with the pack lifecycle ops."""
    for method in ("provision", "prune", "audit"):
        assert hasattr(ISkillProvisionProtocol, method)
    assert hasattr(ISkillProvisionProtocol, '__abstractmethods__')


def test_skill_registry_protocol_exists():
    """CP-SKILL-001b: ISkillRegistryProtocol is an ABC with the listing / install ops."""
    for method in ("list", "check", "show", "install", "uninstall", "sync"):
        assert hasattr(ISkillRegistryProtocol, method)
    assert hasattr(ISkillRegistryProtocol, '__abstractmethods__')


def test_skill_aggregate_exists():
    """CP-SKILL-002: ISkillAggregate is an ABC declaring exactly one entry point."""
    assert hasattr(ISkillAggregate, 'execute')
    assert hasattr(ISkillAggregate, '__abstractmethods__')


def test_skill_aggregate_declares_only_execute():
    """CP-SKILL-002b: the aggregate exposes exactly one abstract method."""
    abstract = {
        name
        for name in vars(ISkillAggregate)
        if callable(getattr(ISkillAggregate, name, None))
        and getattr(getattr(ISkillAggregate, name), "__isabstractmethod__", False)
    }
    assert abstract == {"execute"}


def test_skill_pack_provisioner_implements_protocol():
    """CP-SKILL-003: SkillPackProvisioner implements ISkillProvisionProtocol."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    assert isinstance(provisioner, ISkillProvisionProtocol)
    assert callable(provisioner.provision)
    assert callable(provisioner.prune)
    assert callable(provisioner.audit)


def test_skill_orchestrator_implements_aggregate():
    """CP-SKILL-004: SkillOrchestrator implements ISkillAggregate."""
    from unittest.mock import MagicMock

    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    registry = MagicMock()
    orchestrator = SkillOrchestrator(provisioner, registry)

    assert isinstance(orchestrator, ISkillAggregate)
    assert callable(orchestrator.execute)


def test_skill_registry_adapter_implements_protocol():
    """CP-SKILL-005: SkillRegistryAdapter implements ISkillRegistryProtocol."""
    from modules.skill.src.surface_skill_command import SkillRegistryAdapter

    adapter = SkillRegistryAdapter()
    assert isinstance(adapter, ISkillRegistryProtocol)


def test_skill_registry_adapter_has_registry_methods():
    """CP-SKILL-006: SkillRegistryAdapter exposes the rich registry methods."""
    from modules.skill.src.surface_skill_command import SkillRegistryAdapter

    adapter = SkillRegistryAdapter()
    for method in ("list", "check", "show", "install", "uninstall", "sync"):
        assert callable(getattr(adapter, method))


def test_skill_pack_provisioner_audit_runs():
    """CP-SKILL-007: SkillPackProvisioner.audit reports pack findings."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    assert isinstance(provisioner.audit(), list)


def test_skill_orchestrator_execute_delegates():
    """CP-SKILL-008: SkillOrchestrator.execute routes to provisioner or registry."""
    from unittest.mock import MagicMock

    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
    from modules.shared.src.taxonomy_skill_vo import SkillOp, SkillRequest, SkillToolId

    provisioner = MagicMock()
    provisioner.provision.return_value.success = True
    registry = MagicMock()
    orchestrator = SkillOrchestrator(provisioner, registry)

    # Provisioner path
    orchestrator.execute(SkillRequest(SkillOp("provision"), skill=SkillToolId("test-skill")))
    provisioner.provision.assert_called_once()

    # Registry path
    orchestrator.execute(SkillRequest(SkillOp("list")))
    registry.list.assert_called_once()


def test_root_container_wires_components():
    """CP-SKILL-009: SkillContainer wires provisioner + registry + orchestrator."""
    from modules.skill.src.root_skill_container import SkillContainer

    container = SkillContainer()
    assert hasattr(container, 'aggregate')
    assert isinstance(container.aggregate, ISkillAggregate)


def test_create_skill_feature_returns_aggregate():
    """CP-SKILL-010: create_skill_feature returns ISkillAggregate."""
    from modules.skill.src.root_skill_container import create_skill_feature

    feature = create_skill_feature()
    assert isinstance(feature, ISkillAggregate)
