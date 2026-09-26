"""Contract tests for modules/config — prove protocol/aggregate implementations exist."""
from __future__ import annotations


def test_config_protocol_exists():
    """CP-CONFIG-001: IConfigReaderProtocol and IConfigModifierProtocol are importable."""
    from modules.shared.src.contract_config_protocol import (
        IConfigReaderProtocol,
        IConfigModifierProtocol,
    )

    assert IConfigReaderProtocol is not None
    assert IConfigModifierProtocol is not None


def test_config_reader_seam_has_read_ops():
    """CP-CONFIG-001b: the reader seam carries load/save/inspect/help."""
    from modules.shared.src.contract_config_protocol import IConfigReaderProtocol

    for op in ("load", "save", "inspect", "help"):
        assert hasattr(IConfigReaderProtocol, op), op


def test_config_modifier_seam_has_mutating_ops():
    """CP-CONFIG-001c: the modifier seam carries merge/set/remove/help."""
    from modules.shared.src.contract_config_protocol import IConfigModifierProtocol

    for op in ("merge_servers", "set_env", "remove_entries", "help"):
        assert hasattr(IConfigModifierProtocol, op), op


def test_config_aggregate_has_single_execute():
    """CP-CONFIG-002: IConfigAggregate exposes exactly one ``execute`` entry point."""
    from modules.shared.src.contract_config_aggregate import IConfigAggregate

    assert callable(IConfigAggregate.execute)
    abstract = {
        name
        for name in vars(IConfigAggregate)
        if getattr(getattr(IConfigAggregate, name), "__isabstractmethod__", False)
    }
    assert abstract == {"execute"}


def test_config_request_and_result_vos():
    """CP-CONFIG-003: ConfigRequest/ConfigResult VOs carry the aggregate payload."""
    from pathlib import Path

    from modules.shared.src.taxonomy_common_vo import ConfigRequest, ConfigResult

    request = ConfigRequest("load", path=Path("/tmp/x.json"))
    assert request.op == "load"
    assert request.path == Path("/tmp/x.json")
    assert request.dry_run is False

    result = ConfigResult(True, {"a": 1})
    assert result.success is True
    assert result.data == {"a": 1}
    assert result.message == ""


def test_config_writer_class_exists():
    """CP-CONFIG-004: ConfigWriter class exists and is instantiable."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    writer = ConfigWriter()
    assert isinstance(writer, ConfigWriter)
    assert callable(writer.load)
    assert callable(writer.save)


def test_config_modifier_class_exists():
    """CP-CONFIG-005: ConfigModifier class exists and is instantiable."""
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    modifier = ConfigModifier()
    assert isinstance(modifier, ConfigModifier)
    assert callable(modifier.merge_servers)
    assert callable(modifier.set_env)


def test_config_orchestrator_class_exists():
    """CP-CONFIG-006: ConfigOrchestrator class exists and is instantiable."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)
    assert isinstance(orch, ConfigOrchestrator)
    assert callable(orch.execute)
    assert repr(orch) == "ConfigOrchestrator()"


def test_config_writer_implements_reader_seam():
    """CP-CONFIG-007: ConfigWriter implements the reader seam and nothing more."""
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.contract_config_protocol import (
        IConfigModifierProtocol,
        IConfigReaderProtocol,
    )

    writer = ConfigWriter()
    assert isinstance(writer, IConfigReaderProtocol)
    for op in ("load", "save", "inspect", "help"):
        assert callable(getattr(writer, op))
    assert not isinstance(writer, IConfigModifierProtocol)


def test_config_modifier_implements_modifier_seam():
    """CP-CONFIG-008: ConfigModifier implements the modifier seam and nothing more."""
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.shared.src.contract_config_protocol import (
        IConfigModifierProtocol,
        IConfigReaderProtocol,
    )

    modifier = ConfigModifier()
    assert isinstance(modifier, IConfigModifierProtocol)
    for op in ("merge_servers", "set_env", "remove_entries", "help"):
        assert callable(getattr(modifier, op))
    assert not isinstance(modifier, IConfigReaderProtocol)


def test_no_config_capability_carries_a_stub():
    """CP-CONFIG-016: no config capability raises NotImplementedError (AES304/Rule 4)."""
    from pathlib import Path

    config_src = Path("modules/config/src")
    offenders = [
        f.name
        for f in config_src.glob("*.py")
        if "raise NotImplementedError" in f.read_text()
    ]
    assert offenders == [], f"NotImplementedError stubs remain in: {offenders}"


def test_config_orchestrator_implements_aggregate():
    """CP-CONFIG-009: ConfigOrchestrator implements IConfigAggregate."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.shared.src.contract_config_aggregate import IConfigAggregate
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.config.src.capabilities_config_modifier import ConfigModifier

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)
    assert isinstance(orch, IConfigAggregate)


def test_config_container_provides_feature():
    """CP-CONFIG-010: ConfigContainer provides IConfigAggregate feature."""
    from modules.config.src.root_config_container import ConfigContainer
    from modules.shared.src.contract_config_aggregate import IConfigAggregate

    container = ConfigContainer()
    aggregate = container.aggregate
    assert isinstance(aggregate, IConfigAggregate)


def test_create_config_feature_provides_aggregate():
    """CP-CONFIG-011: create_config_feature returns IConfigAggregate."""
    from modules.config.src.root_config_container import create_config_feature
    from modules.shared.src.contract_config_aggregate import IConfigAggregate

    feature = create_config_feature()
    assert isinstance(feature, IConfigAggregate)


def test_config_surface_command_class_exists():
    """CP-CONFIG-012: ConfigCommand surface class exists and implements the aggregate."""
    from modules.config.src.surface_config_command import ConfigCommand
    from modules.shared.src.contract_config_aggregate import IConfigAggregate

    assert hasattr(ConfigCommand, "__init__")
    assert issubclass(ConfigCommand, IConfigAggregate)
    assert callable(ConfigCommand.execute)


def test_cmd_config_function_exists():
    """CP-CONFIG-013: cmd_config entry function exists."""
    from modules.config.src.surface_config_command import cmd_config

    assert callable(cmd_config)


def test_config_agent_exports():
    """CP-CONFIG-014: Config module exports required symbols."""
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.config.src.capabilities_config_modifier import ConfigModifier
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
    """CP-CONFIG-015: modules.config package exports public symbols."""
    import modules.config

    assert hasattr(modules.config, "ConfigOrchestrator")
    assert hasattr(modules.config, "ConfigContainer")
    assert hasattr(modules.config, "create_config_feature")
