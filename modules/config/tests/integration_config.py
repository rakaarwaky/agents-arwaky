"""Integration tests for modules/config — full feature workflows."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path


def test_config_load_save_roundtrip_json():
    """IT-CONFIG-001: Full load/save roundtrip on JSON file."""
    from modules.config.src.capabilities_config_engine import ConfigWriter
    from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat

    writer = ConfigWriter()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"existing": "value"}')
        f.flush()
        path = Path(f.name)

    try:
        data, fmt = writer.load_file(path)
        assert fmt == "json"
        assert data["existing"] == "value"

        data["new_key"] = "new_value"
        writer.save_file(path, ConfigData(data), ConfigFormat("json"))

        data2, _ = writer.load_file(path)
        assert data2["existing"] == "value"
        assert data2["new_key"] == "new_value"
    finally:
        path.unlink(missing_ok=True)


def test_config_detect_format_various():
    """IT-CONFIG-002: detect_format identifies JSON, TOML, YAML correctly."""
    from modules.config.src.capabilities_config_engine import ConfigWriter

    writer = ConfigWriter()
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "config.json"
        json_path.write_text("{}")
        assert writer.detect_format(json_path) == "json"

        toml_path = Path(tmpdir) / "config.toml"
        toml_path.write_text('[section]\nkey = "value"')
        assert writer.detect_format(toml_path) == "toml"

        yaml_path = Path(tmpdir) / "config.yaml"
        yaml_path.write_text("key: value\n")
        assert writer.detect_format(yaml_path) == "yaml"


def test_config_orchestrator_full_workflow():
    """IT-CONFIG-003: End-to-end orchestrator workflow with real files."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_engine import ConfigModifier, ConfigWriter
    from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    try:
        saved = orch.save(path, ConfigData({"mcpServers": {}}), ConfigFormat("json"))
        assert saved is True

        snap = orch.inspect(path)
        assert snap["format"] == "json"

        merged = orch.merge_servers(path, {"my-server": {"url": "http://example.com"}})
        assert "my-server" in merged

        servers = orch.inspect(path)
        assert "my-server" in servers["servers"]
    finally:
        path.unlink(missing_ok=True)


def test_config_env_integration():
    """IT-CONFIG-004: Full env file set/remove workflow."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_engine import ConfigModifier, ConfigWriter

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("# initial\nKEY1=value1\n")
        f.flush()
        path = Path(f.name)

    try:
        orch.set_env(path, {"KEY2": "value2", "KEY3": "value3"})

        content = path.read_text()
        assert "KEY1=value1" in content
        # set_env may quote values, so check key presence
        assert "KEY2=" in content
        assert "KEY3=" in content

        removed = orch.remove_entries(path, ["KEY2"])
        assert "KEY2" in removed

        content = path.read_text()
        assert "KEY2" not in content
        assert "KEY3=" in content
    finally:
        path.unlink(missing_ok=True)


def test_config_orchestrator_inspect():
    """IT-CONFIG-005: inspect returns complete snapshot."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_engine import ConfigModifier, ConfigWriter
    from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"mcpServers": {"server1": {"url": "http://test"}}}')
        f.flush()
        path = Path(f.name)

    try:
        snap = orch.inspect(path)
        assert snap["path"] == str(path)
        assert snap["format"] == "json"
        assert snap["data"] == {"mcpServers": {"server1": {"url": "http://test"}}}
        assert "server1" in snap["servers"]
    finally:
        path.unlink(missing_ok=True)


def test_config_dry_run_remove():
    """IT-CONFIG-006: remove_entries dry-run reports without writing."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_engine import ConfigModifier, ConfigWriter

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(json.dumps({"mcpServers": {"server1": {}, "server2": {}}}))
        f.flush()
        path = Path(f.name)

    try:
        removed = orch.remove_entries(path, ["server1"], dry_run=True)
        assert "server1" in removed

        content = json.loads(path.read_text())
        assert "server1" in content["mcpServers"]
    finally:
        path.unlink(missing_ok=True)


def test_config_command_integration():
    """IT-CONFIG-007: ConfigCommand surface integrates with orchestrator."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_engine import ConfigModifier, ConfigWriter
    from modules.config.src.surface_config_command import ConfigCommand

    writer = ConfigWriter()
    modifier = ConfigModifier()
    orch = ConfigOrchestrator(writer, modifier)
    cmd = ConfigCommand(orch)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    try:
        snap = cmd.inspect(path)
        assert snap is not None
        assert snap["format"] == "json"

        help_text = cmd.help()
        assert "Usage: aa config" in str(help_text)
    finally:
        path.unlink(missing_ok=True)


def test_config_container_wiring():
    """IT-CONFIG-008: ConfigContainer produces fully wired feature."""
    from modules.config.src.root_config_container import ConfigContainer
    from modules.shared.src.contract_config_aggregate import IConfigAggregate

    container = ConfigContainer()
    aggregate = container.aggregate
    assert isinstance(aggregate, IConfigAggregate)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    try:
        snap = aggregate.inspect(path)
        assert snap["format"] == "json"
    finally:
        path.unlink(missing_ok=True)
