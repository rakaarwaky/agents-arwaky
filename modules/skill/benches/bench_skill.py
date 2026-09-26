"""Benchmarks for modules/skill — performance testing."""
from __future__ import annotations


def bench_pack_provisioner_init(benchmark):
    """BENCH-SKILL-001: Benchmark SkillPackProvisioner initialization."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    benchmark(SkillPackProvisioner)


def bench_orchestrator_init(benchmark):
    """BENCH-SKILL-002: Benchmark SkillOrchestrator initialization."""
    from unittest.mock import MagicMock
    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    registry = MagicMock()

    benchmark(SkillOrchestrator, provisioner, registry)


def bench_registry_adapter_init(benchmark):
    """BENCH-SKILL-003: Benchmark SkillRegistryAdapter initialization."""
    from modules.skill.src.surface_skill_command import SkillRegistryAdapter

    benchmark(SkillRegistryAdapter)


def bench_container_creation(benchmark):
    """BENCH-SKILL-004: Benchmark SkillContainer creation."""
    from modules.skill.src.root_skill_container import SkillContainer

    benchmark(SkillContainer)


def bench_create_skill_feature(benchmark):
    """BENCH-SKILL-005: Benchmark create_skill_feature."""
    from modules.skill.src.root_skill_container import create_skill_feature

    benchmark(create_skill_feature)


def bench_pack_provisioner_execute_audit(benchmark):
    """BENCH-SKILL-006: Benchmark SkillPackProvisioner.execute('audit')."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()

    benchmark(provisioner.execute, "audit")


def bench_pack_provisioner_execute_provision(benchmark):
    """BENCH-SKILL-007: Benchmark SkillPackProvisioner.execute('provision')."""
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()

    benchmark(provisioner.execute, "provision", "lint")


def bench_orchestrator_execute_provision(benchmark):
    """BENCH-SKILL-008: Benchmark SkillOrchestrator.execute('provision')."""
    from unittest.mock import MagicMock
    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    registry = MagicMock()
    orchestrator = SkillOrchestrator(provisioner, registry)

    benchmark(orchestrator.execute, "provision", "lint")


def bench_orchestrator_list(benchmark):
    """BENCH-SKILL-009: Benchmark SkillOrchestrator.list()."""
    from unittest.mock import MagicMock
    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    registry = MagicMock()
    orchestrator = SkillOrchestrator(provisioner, registry)

    benchmark(orchestrator.list)


def bench_orchestrator_check(benchmark):
    """BENCH-SKILL-010: Benchmark SkillOrchestrator.check()."""
    from unittest.mock import MagicMock
    from modules.skill.src.agent_skill_orchestrator import SkillOrchestrator
    from modules.skill.src.capabilities_skill_pack import SkillPackProvisioner

    provisioner = SkillPackProvisioner()
    registry = MagicMock()
    orchestrator = SkillOrchestrator(provisioner, registry)

    benchmark(orchestrator.check)
