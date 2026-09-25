"""Contract tests for modules/harness — verify protocol implementations."""
from __future__ import annotations


def test_harness_protocol_exists():
    """CP-HARNESS-001: IHarnessProtocol exists and can be imported."""
    from modules.shared.src.contract_harness_protocol import IHarnessProtocol

    assert IHarnessProtocol is not None


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


def test_harness_connectors_implement_protocol():
    """CP-HARNESS-006: Harness connectors implement IHarnessProtocol."""
    from modules.harness.src.capabilities_harness_connector import HarnessConnector
    from modules.harness.src.capabilities_harness_disconnector import HarnessDisconnector
    from modules.harness.src.capabilities_harness_skills import HarnessSkills
    from modules.shared.src.contract_harness_protocol import IHarnessProtocol

    connector = HarnessConnector({})
    disconnector = HarnessDisconnector({})
    skills = HarnessSkills({})

    assert isinstance(connector, IHarnessProtocol)
    assert isinstance(disconnector, IHarnessProtocol)
    assert isinstance(skills, IHarnessProtocol)


def test_harness_leaf_adapters_implement_protocol():
    """CP-HARNESS-007: every provider leaf implements IHarnessProtocol (AES403)."""
    from modules.harness.src.capabilities_harness_grok_build_adapter import (
        GrokBuildHarnessAdapter,
    )
    from modules.harness.src.capabilities_harness_hermes_adapter import (
        HermesHarnessAdapter,
    )
    from modules.harness.src.capabilities_harness_opencode_adapter import (
        OpencodeHarnessAdapter,
    )
    from modules.shared.src.contract_harness_protocol import IHarnessProtocol

    leaf_classes = (
        GrokBuildHarnessAdapter,
        HermesHarnessAdapter,
        OpencodeHarnessAdapter,
    )

    for adapter_cls in leaf_classes:
        assert issubclass(adapter_cls, IHarnessProtocol)
        assert isinstance(adapter_cls(), IHarnessProtocol)


def test_harness_registry_wires_every_supported_id():
    """CP-HARNESS-008: the root registry carries one leaf per supported id."""
    from modules.harness.src.root_harness_container import HARNESS_REGISTRY
    from modules.shared.src.taxonomy_harness_constant import ALL_HARNESS_IDS

    assert sorted(HARNESS_REGISTRY) == sorted(ALL_HARNESS_IDS)
