"""Contract tests for modules/skill — prove protocol/interface implementations exist."""
from __future__ import annotations

from pathlib import Path

from modules.shared.src.contract_skill_aggregate import ISkillAggregate
from modules.shared.src.contract_skill_protocol import ISkillProtocol


def test_skill_protocol_exists():
    """CP-SKILL-001: ISkillProtocol is an ABC with execute method."""
    assert hasattr(ISkillProtocol, 'execute')
    assert hasattr(ISkillProtocol, '__abstractmethods__')


def test_skill_aggregate_exists():
    """CP-SKILL-002: ISkillAggregate is an ABC with required methods."""
    assert hasattr(ISkillAggregate, 'list')
    assert hasattr(ISkillAggregate, 'check')
    assert hasattr(ISkillAggregate, 'install')
    assert hasattr(ISkillAggregate, 'uninstall')
    assert hasattr(ISkillAggregate, 'show')
    assert hasattr(ISkillAggregate, 'sync')
    assert hasattr(ISkillAggregate, '__abstractmethods__')


def test_skill_pack_provisioner_implements_protocol():
    """CP-SKILL-003: SkillPackProvisioner implements ISkillProtocol."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    assert isinstance(provisioner, ISkillProtocol)
    assert callable(provisioner.execute)


def test_skill_orchestrator_implements_aggregate():
    """CP-SKILL-004: SkillOrchestrator implements ISkillAggregate."""
    from unittest.mock import MagicMock
    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    registry = MagicMock()
    orchestrator = SkillOrchestrator(provisioner, registry)

    assert isinstance(orchestrator, ISkillAggregate)
    assert callable(orchestrator.list)
    assert callable(orchestrator.check)
    assert callable(orchestrator.install)
    assert callable(orchestrator.uninstall)
    assert callable(orchestrator.show)
    assert callable(orchestrator.sync)


def test_skill_registry_adapter_implements_protocol():
    """CP-SKILL-005: SkillRegistryAdapter implements ISkillProtocol."""
    from modules.skill.src.surface_skill_command import SkillRegistryAdapter

    adapter = SkillRegistryAdapter()
    assert isinstance(adapter, ISkillProtocol)
    assert callable(adapter.execute)


def test_skill_registry_adapter_has_registry_methods():
    """CP-SKILL-006: SkillRegistryAdapter exposes aggregate-named methods."""
    from modules.skill.src.surface_skill_command import SkillRegistryAdapter

    adapter = SkillRegistryAdapter()
    assert callable(adapter.list)
    assert callable(adapter.check)
    assert callable(adapter.show)
    assert callable(adapter.install)
    assert callable(adapter.uninstall)
    assert callable(adapter.sync)


def test_skill_pack_provisioner_execute_dispatches():
    """CP-SKILL-007: SkillPackProvisioner.execute dispatches known ops."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    # audit should not raise (returns int based on findings)
    result = provisioner.execute("audit")
    assert isinstance(result, int)


def test_skill_orchestrator_execute_delegates():
    """CP-SKILL-008: SkillOrchestrator.execute routes to provisioner or registry."""
    from unittest.mock import MagicMock
    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = MagicMock()
    registry = MagicMock()
    orchestrator = SkillOrchestrator(provisioner, registry)

    # Provisioner path
    orchestrator.execute("provision", "test-skill")
    provisioner.execute.assert_called_with("provision", "test-skill", None)

    # Registry path
    orchestrator.execute("list")
    registry.execute.assert_called_with("list", None, None)


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
