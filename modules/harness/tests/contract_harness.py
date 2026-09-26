"""Contract tests for modules/harness — verify protocol implementations."""
from __future__ import annotations


def test_harness_protocols_exist():
    """CP-HARNESS-001: all four seam ABCs exist and can be imported."""
    from modules.shared.src.contract_harness_protocol import (
        IHarnessConnectProtocol,
        IHarnessDisconnectProtocol,
        IHarnessProviderProtocol,
        IHarnessSkillsProtocol,
    )

    assert IHarnessConnectProtocol is not None
    assert IHarnessDisconnectProtocol is not None
    assert IHarnessProviderProtocol is not None
    assert IHarnessSkillsProtocol is not None


def test_harness_connector_exists():
    """CP-HARNESS-002: HarnessConnector class exists."""
    from modules.harness.src.capabilities_harness_connector import HarnessConnector

    assert HarnessConnector is not None


def test_harness_disconnector_exists():
    """CP-HARNESS-003: HarnessDisconnector class exists."""
    from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector

    assert HarnessDisconnector is not None


def test_harness_skills_exists():
    """CP-HARNESS-004: HarnessSkills class exists."""
    from modules.harness.src.capabilities_harness_skills import HarnessSkills

    assert HarnessSkills is not None


def test_harness_orchestrator_exists():
    """CP-HARNESS-005: HarnessOrchestrator class exists."""
    from modules.harness.src.agent_harness_orchestrator import HarnessOrchestrator

    assert HarnessOrchestrator is not None


def test_harness_connectors_implement_operations_protocol():
    """CP-HARNESS-006: each business capability implements exactly its own seam."""
    from modules.harness.src.capabilities_harness_connector import HarnessConnector
    from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector
    from modules.harness.src.capabilities_harness_skills import HarnessSkills
    from modules.shared.src.contract_harness_protocol import (
        IHarnessConnectProtocol,
        IHarnessDisconnectProtocol,
        IHarnessSkillsProtocol,
    )

    connector = HarnessConnector({})
    disconnector = HarnessDisconnector({})
    skills = HarnessSkills({})

    assert isinstance(connector, IHarnessConnectProtocol)
    assert isinstance(disconnector, IHarnessDisconnectProtocol)
    assert isinstance(skills, IHarnessSkillsProtocol)


def test_each_business_capability_implements_exactly_one_seam():
    """CP-HARNESS-010: a capability carries one seam ABC, never a second."""
    from modules.harness.src.capabilities_harness_connector import HarnessConnector
    from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector
    from modules.harness.src.capabilities_harness_skills import HarnessSkills
    from modules.shared.src.contract_harness_protocol import (
        IHarnessConnectProtocol,
        IHarnessDisconnectProtocol,
        IHarnessSkillsProtocol,
    )

    seams = (
        IHarnessConnectProtocol,
        IHarnessDisconnectProtocol,
        IHarnessSkillsProtocol,
    )
    for capability in (HarnessConnector, HarnessDisconnector, HarnessSkills):
        owned = [seam for seam in seams if issubclass(capability, seam)]
        assert len(owned) == 1, f"{capability.__name__} implements {len(owned)} seams"


def test_harness_leaf_adapters_implement_provider_protocol():
    """CP-HARNESS-007: every provider leaf implements the provider seam (AES403)."""
    from modules.harness.src.capabilities_harness_grok_build_adapter import (
        GrokBuildHarnessAdapter,
    )
    from modules.harness.src.capabilities_harness_hermes_adapter import (
        HermesHarnessAdapter,
    )
    from modules.harness.src.capabilities_harness_opencode_adapter import (
        OpencodeHarnessAdapter,
    )
    from modules.shared.src.contract_harness_protocol import IHarnessProviderProtocol

    leaf_classes = (
        GrokBuildHarnessAdapter,
        HermesHarnessAdapter,
        OpencodeHarnessAdapter,
    )

    for adapter_cls in leaf_classes:
        assert issubclass(adapter_cls, IHarnessProviderProtocol)
        assert isinstance(adapter_cls(), IHarnessProviderProtocol)


def test_no_capability_carries_a_stub():
    """CP-HARNESS-009: no harness capability raises NotImplementedError (AES304/Rule 4)."""
    from importlib import import_module
    from pathlib import Path

    harness_src = Path("modules/harness/src")
    offenders = [
        f.name
        for f in harness_src.glob("*.py")
        if "raise NotImplementedError" in f.read_text()
    ]
    assert offenders == [], f"NotImplementedError stubs remain in: {offenders}"


def test_harness_registry_wires_every_supported_id():
    """CP-HARNESS-008: the root registry carries one leaf per supported id."""
    from modules.harness.src.root_harness_container import HARNESS_REGISTRY
    from modules.shared.src.taxonomy_harness_constant import ALL_HARNESS_IDS

    assert sorted(HARNESS_REGISTRY) == sorted(ALL_HARNESS_IDS)
