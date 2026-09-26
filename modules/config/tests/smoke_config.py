"""Smoke tests for modules/config — fast boot and import checks."""
from __future__ import annotations

import time


def test_import_config_module():
    """SM-CONFIG-001: modules.config can be imported."""
    import modules.config
    assert modules.config is not None


def test_import_config_src():
    """SM-CONFIG-002: modules.config.src can be imported."""
    from modules.config import src
    assert src is not None


def test_import_config_writer():
    """SM-CONFIG-003: ConfigWriter can be imported."""
    from modules.config.src.capabilities_config_writer import ConfigWriter
    assert ConfigWriter is not None


def test_import_config_modifier():
    """SM-CONFIG-004: ConfigModifier can be imported."""
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    assert ConfigModifier is not None


def test_import_config_orchestrator():
    """SM-CONFIG-005: ConfigOrchestrator can be imported."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    assert ConfigOrchestrator is not None


def test_import_config_container():
    """SM-CONFIG-006: ConfigContainer and factory can be imported."""
    from modules.config.src.root_config_container import ConfigContainer, create_config_feature
    assert ConfigContainer is not None
    assert callable(create_config_feature)


def test_import_config_command():
    """SM-CONFIG-007: ConfigCommand and cmd_config can be imported."""
    from modules.config.src.surface_config_command import ConfigCommand, cmd_config
    assert ConfigCommand is not None
    assert callable(cmd_config)


def test_import_config_protocol():
    """SM-CONFIG-008: both config seam ABCs can be imported."""
    from modules.shared.src.contract_config_protocol import (
        IConfigReaderProtocol,
        IConfigModifierProtocol,
    )
    assert IConfigReaderProtocol is not None
    assert IConfigModifierProtocol is not None


def test_import_config_aggregate():
    """SM-CONFIG-009: IConfigAggregate can be imported."""
    from modules.shared.src.contract_config_aggregate import IConfigAggregate
    assert IConfigAggregate is not None


def test_config_writer_instantiation_quick():
    """SM-CONFIG-010: ConfigWriter instantiation completes within 1 second."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    start = time.time()
    writer = ConfigWriter()
    elapsed = time.time() - start

    assert elapsed < 1.0
    assert writer is not None


def test_config_modifier_instantiation_quick():
    """SM-CONFIG-011: ConfigModifier instantiation completes within 1 second."""
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    start = time.time()
    modifier = ConfigModifier()
    elapsed = time.time() - start

    assert elapsed < 1.0
    assert modifier is not None


def test_config_orchestrator_instantiation_quick():
    """SM-CONFIG-012: ConfigOrchestrator instantiation completes within 1 second."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    start = time.time()
    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)
    elapsed = time.time() - start

    assert elapsed < 1.0
    assert orch is not None


def test_config_container_instantiation_quick():
    """SM-CONFIG-013: ConfigContainer instantiation completes within 1 second."""
    from modules.config.src.root_config_container import ConfigContainer

    start = time.time()
    container = ConfigContainer()
    elapsed = time.time() - start

    assert elapsed < 1.0
    assert container.aggregate is not None


def test_create_config_feature_quick():
    """SM-CONFIG-014: create_config_feature completes within 1 second."""
    from modules.config.src.root_config_container import create_config_feature

    start = time.time()
    feature = create_config_feature()
    elapsed = time.time() - start

    assert elapsed < 1.0
    assert feature is not None
