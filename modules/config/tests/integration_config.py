"""Integration tests for modules/config — full feature workflows."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path


def test_config_load_save_roundtrip_json():
    """IT-CONFIG-001: Full load/save roundtrip on JSON file."""
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.common.taxonomy_common_vo import ConfigData, ConfigFormat

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


def test_config_roundtrip_jsonc_byte_identical(tmp_path):
    """CFG-01: saving an unchanged JSONC document preserves every byte."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    original = (
        b"// keep this heading and formatting\n"
        b"{\n"
        b'  "mcpServers": {\n'
        b'    "alpha": {"command": "node", "args": ["serve"]}\n'
        b"  }\n"
        b"}\n"
    )
    path = tmp_path / "settings.jsonc"
    path.write_bytes(original)

    writer = ConfigWriter()
    data, fmt = writer.load_file(path)
    assert fmt == "jsonc"
    assert writer.save_file(path, data, fmt) is True
    assert path.read_bytes() == original


def test_config_roundtrip_toml_byte_identical(tmp_path):
    """CFG-01: saving an unchanged TOML document preserves comments and bytes."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

    original = (
        b"# provider configuration\n"
        b"[servers.alpha]\n"
        b'command = "node"\n'
        b'args = ["serve", "--mcp"]\n'
    )
    path = tmp_path / "settings.toml"
    path.write_bytes(original)

    writer = ConfigWriter()
    data, fmt = writer.load_file(path)
    assert fmt == "toml"
    assert writer.save_file(path, data, fmt) is True
    assert path.read_bytes() == original


def test_config_dry_run_remove_purity(tmp_path):
    """CFG-01: aggregate dry-run reports removals without changing file bytes."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.common.taxonomy_common_vo import (
        ConfigKeys,
        ConfigOp,
        ConfigRequest,
    )

    path = tmp_path / "servers.json"
    original = b'{\n  "mcpServers": {"alpha": {}, "beta": {}}\n}\n'
    path.write_bytes(original)
    aggregate = ConfigOrchestrator(ConfigWriter(), ConfigModifier())

    result = aggregate.execute(
        ConfigRequest(
            ConfigOp("remove_entries"),
            path=path,
            keys=ConfigKeys(["alpha"]),
            dry_run=True,
        )
    )

    assert result.success is True
    assert result.data == ["alpha"]
    assert path.read_bytes() == original


def test_config_cli_live_execute(tmp_path, capsys):
    """CFG-04: inspect and load CLI verbs execute through the aggregate."""
    from modules.cli.src.surface_config_command import ConfigCommand, cmd_config
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter

    path = tmp_path / "client.json"
    path.write_text('{"mcpServers": {"alpha": {"command": "node"}}}\n', encoding="utf-8")
    aggregate = ConfigOrchestrator(ConfigWriter(), ConfigModifier())
    command = ConfigCommand(aggregate)

    assert cmd_config(["inspect", str(path)], command) == 0
    inspected = capsys.readouterr().out
    assert '"format": "json"' in inspected
    assert '"alpha"' in inspected

    assert cmd_config(["load", str(path)], command) == 0
    loaded = capsys.readouterr().out
    assert '"format": "json"' in loaded
    assert '"command": "node"' in loaded


def test_config_detect_format_various():
    """IT-CONFIG-002: detect_format identifies JSON, TOML, YAML correctly."""
    from modules.config.src.capabilities_config_writer import ConfigWriter

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
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.common.taxonomy_common_vo import (
        ConfigData,
        ConfigFormat,
        ConfigOp,
        ConfigRequest,
        McpServersMap,
    )

    orch = ConfigOrchestrator(ConfigWriter(), ConfigModifier())

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    try:
        saved = orch.execute(
            ConfigRequest(
                ConfigOp("save"),
                path=path,
                data=ConfigData({"mcpServers": {}}),
                fmt=ConfigFormat("json"),
            )
        )
        assert saved.success is True

        snap = orch.execute(ConfigRequest(ConfigOp("inspect"), path=path))
        assert snap.data["format"] == "json"

        merged = orch.execute(
            ConfigRequest(
                ConfigOp("merge_servers"),
                path=path,
                servers=McpServersMap({"my-server": {"url": "http://example.com"}}),
            )
        )
        assert "my-server" in merged.data

        servers = orch.execute(ConfigRequest(ConfigOp("inspect"), path=path))
        assert "my-server" in servers.data["servers"]
    finally:
        path.unlink(missing_ok=True)


def test_config_env_integration():
    """IT-CONFIG-004: Full env file set/remove workflow."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.common.taxonomy_common_vo import (
        ConfigKeys,
        ConfigOp,
        ConfigRequest,
        EnvPairs,
    )

    orch = ConfigOrchestrator(ConfigWriter(), ConfigModifier())

    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("# initial\nKEY1=value1\n")
        f.flush()
        path = Path(f.name)

    try:
        set_result = orch.execute(
            ConfigRequest(
                ConfigOp("set_env"),
                path=path,
                pairs=EnvPairs({"KEY2": "value2", "KEY3": "value3"}),
            )
        )
        assert set_result.success is True

        content = path.read_text()
        assert "KEY1=value1" in content
        # set_env may quote values, so check key presence
        assert "KEY2=" in content
        assert "KEY3=" in content

        removed = orch.execute(
            ConfigRequest(ConfigOp("remove_entries"), path=path, keys=ConfigKeys(["KEY2"]))
        )
        assert "KEY2" in removed.data

        content = path.read_text()
        assert "KEY2" not in content
        assert "KEY3=" in content
    finally:
        path.unlink(missing_ok=True)


def test_config_orchestrator_inspect():
    """IT-CONFIG-005: execute(inspect) returns a complete snapshot."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.common.taxonomy_common_vo import ConfigOp, ConfigRequest

    orch = ConfigOrchestrator(ConfigWriter(), ConfigModifier())

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"mcpServers": {"server1": {"url": "http://test"}}}')
        f.flush()
        path = Path(f.name)

    try:
        result = orch.execute(ConfigRequest(ConfigOp("inspect"), path=path))
        assert result.success is True
        snap = result.data
        assert snap["path"] == str(path)
        assert snap["format"] == "json"
        assert snap["data"] == {"mcpServers": {"server1": {"url": "http://test"}}}
        assert "server1" in snap["servers"]
    finally:
        path.unlink(missing_ok=True)


def test_config_dry_run_remove():
    """IT-CONFIG-006: execute(remove_entries, dry_run) reports without writing."""
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.common.taxonomy_common_vo import (
        ConfigKeys,
        ConfigOp,
        ConfigRequest,
    )

    orch = ConfigOrchestrator(ConfigWriter(), ConfigModifier())

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(json.dumps({"mcpServers": {"server1": {}, "server2": {}}}))
        f.flush()
        path = Path(f.name)

    try:
        result = orch.execute(
            ConfigRequest(
                ConfigOp("remove_entries"),
                path=path,
                keys=ConfigKeys(["server1"]),
                dry_run=True,
            )
        )
        assert "server1" in result.data

        content = json.loads(path.read_text())
        assert "server1" in content["mcpServers"]
    finally:
        path.unlink(missing_ok=True)


def test_config_command_integration():
    """IT-CONFIG-007: the CLI surface routes every verb through the aggregate."""
    from modules.cli.src.surface_config_command import ConfigCommand, cmd_config
    from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
    from modules.config.src.capabilities_config_modifier import ConfigModifier
    from modules.config.src.capabilities_config_writer import ConfigWriter
    from modules.shared.src.common.taxonomy_common_vo import ConfigOp, ConfigRequest

    cmd = ConfigCommand(ConfigOrchestrator(ConfigWriter(), ConfigModifier()))

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    try:
        snap = cmd.execute(ConfigRequest(ConfigOp("inspect"), path=path))
        assert snap.success is True
        assert snap.data["format"] == "json"

        assert cmd.execute(ConfigRequest(ConfigOp("help"))).success is True
        assert cmd_config(["inspect", str(path)], cmd) == 0
    finally:
        path.unlink(missing_ok=True)


def test_config_container_wiring():
    """IT-CONFIG-008: ConfigContainer produces fully wired feature."""
    from modules.config.src.root_config_container import ConfigContainer
    from modules.shared.src.common.taxonomy_common_vo import ConfigOp, ConfigRequest
    from modules.shared.src.config.contract_config_aggregate import IConfigAggregate

    container = ConfigContainer()
    aggregate = container.aggregate
    assert isinstance(aggregate, IConfigAggregate)
    # The aggregate is the one door: exactly one abstract method.
    assert IConfigAggregate.__abstractmethods__ == frozenset({"execute"})

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{}')
        f.flush()
        path = Path(f.name)

    try:
        snap = aggregate.execute(ConfigRequest(ConfigOp("inspect"), path=path))
        assert snap.success is True
        assert snap.data["format"] == "json"
    finally:
        path.unlink(missing_ok=True)
