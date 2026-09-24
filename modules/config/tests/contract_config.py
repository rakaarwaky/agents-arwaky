"""Contract tests for modules/config — prove protocol/interface implementations exist."""
from __future__ import annotations


def test_config_protocol_exists():
    """CP-CONFIG-001: IConfigProtocol ABC exists and is importable."""
    from modules.shared.src.contract_config_protocol import IConfigProtocol

    assert IConfigProtocol is not None
    assert hasattr(IConfigProtocol, "execute")


def test_config_writer_class_exists():
    """CP-CONFIG-002: ConfigWriter class exists and is instantiable."""
    from modules.config.src.capabilities_config_engine import ConfigWriter

    writer = ConfigWriter()
    assert isinstance(writer, ConfigWriter)
    assert callable(writer.execute)


def test_config_modifier_class_exists():
    """CP-CONFIG-003: ConfigModifier class exists and is instantiable."""
    from modules.config.src.capabilities_config_engine import ConfigModifier

    modifier = ConfigModifier()
    assert isinstance(modifier, ConfigModifier)
    assert callable(modifier.execute)


def test_config_orchestrator_class_exists():
    """CP-CONFIG-004: ConfigOrchestrator class exists and is instantiable."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_engine import ConfigWriter, ConfigModifier

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)
    assert isinstance(orch, ConfigOrchestrator)
    assert callable(orch.load)
    assert callable(orch.save)
    assert callable(orch.inspect)
    assert callable(orch.merge_servers)
    assert callable(orch.set_env)
    assert callable(orch.remove_entries)
    assert callable(orch.help)


def test_config_writer_implements_protocol():
    """CP-CONFIG-005: ConfigWriter implements IConfigProtocol execute."""
    from modules.config.src.capabilities_config_engine import ConfigWriter
    from modules.shared.src.contract_config_protocol import IConfigProtocol

    writer = ConfigWriter()
    assert isinstance(writer, IConfigProtocol)
    assert hasattr(writer, "execute")
    assert callable(writer.execute)


def test_config_modifier_implements_protocol():
    """CP-CONFIG-006: ConfigModifier implements IConfigProtocol execute."""
    from modules.config.src.capabilities_config_engine import ConfigModifier
    from modules.shared.src.contract_config_protocol import IConfigProtocol

    modifier = ConfigModifier()
    assert isinstance(modifier, IConfigProtocol)
    assert hasattr(modifier, "execute")
    assert callable(modifier.execute)


def test_config_orchestrator_implements_aggregate():
    """CP-CONFIG-007: ConfigOrchestrator implements IConfigAggregate."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.shared.src.contract_config_aggregate import IConfigAggregate
    from modules.config.src.capabilities_config_engine import ConfigWriter, ConfigModifier

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)
    assert isinstance(orch, IConfigAggregate)


def test_config_container_provides_feature():
    """CP-CONFIG-008: ConfigContainer provides IConfigAggregate feature."""
    from modules.config.src.root_config_container import ConfigContainer
    from modules.shared.src.contract_config_aggregate import IConfigAggregate

    container = ConfigContainer()
    aggregate = container.aggregate
    assert isinstance(aggregate, IConfigAggregate)


def test_create_config_feature_provides_aggregate():
    """CP-CONFIG-009: create_config_feature returns IConfigAggregate."""
    from modules.config.src.root_config_container import create_config_feature
    from modules.shared.src.contract_config_aggregate import IConfigAggregate

    feature = create_config_feature()
    assert isinstance(feature, IConfigAggregate)


def test_config_surface_command_class_exists():
    """CP-CONFIG-010: ConfigCommand surface class exists."""
    from modules.config.src.surface_config_command import ConfigCommand

    assert ConfigCommand is not None
    assert hasattr(ConfigCommand, "__init__")


def test_cmd_config_function_exists():
    """CP-CONFIG-011: cmd_config entry function exists."""
    from modules.config.src.surface_config_command import cmd_config

    assert callable(cmd_config)


def test_config_agent_exports():
    """CP-CONFIG-012: Config module exports required symbols."""
    from modules.config.src.capabilities_config_engine import ConfigWriter, ConfigModifier
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.surface_config_command import ConfigCommand, cmd_config
    from modules.config.src.root_config_container import ConfigContainer, create_config_feature

    assert ConfigWriter is not None
    assert ConfigModifier is not None
    assert ConfigOrchestrator is not None
    assert ConfigCommand is not None
    assert callable(cmd_config)
    assert ConfigContainer is not None
    assert callable(create_config_feature)


def test_config_module_level_exports():
    """CP-CONFIG-013: modules.config package exports public symbols."""
    import modules.config

    assert hasattr(modules.config, "ConfigOrchestrator")
    assert hasattr(modules.config, "ConfigContainer")
    assert hasattr(modules.config, "create_config_feature")
