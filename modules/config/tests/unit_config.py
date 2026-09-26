"""Unit tests for modules/config — ConfigWriter, ConfigModifier, ConfigOrchestrator."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestConfigWriter:
    """Tests for ConfigWriter capability."""

    def test_init(self):
        """UT-CONFIG-001: ConfigWriter initializes without args."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        assert writer is not None

    def test_load_uses_rich_method(self):
        """UT-CONFIG-002: load() is the named protocol method; there is no execute()."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        assert not hasattr(writer, "execute")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"key": "value"}')
            f.flush()
            path = Path(f.name)

        try:
            data, fmt = writer.load(path)
            assert data["key"] == "value"
            assert fmt == "json"
        finally:
            path.unlink(missing_ok=True)

    def test_save_uses_rich_method(self):
        """UT-CONFIG-003: save() is the named protocol method."""
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat

        writer = ConfigWriter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            f.flush()
            path = Path(f.name)

        try:
            result = writer.save(path, ConfigData({"new_key": "new_value"}), ConfigFormat("json"))
            assert result is True
        finally:
            path.unlink(missing_ok=True)

    def test_inspect_returns_snapshot(self):
        """UT-CONFIG-004: inspect() is the named read-only protocol method."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"key": "value"}')
            f.flush()
            path = Path(f.name)

        try:
            snap = writer.inspect(path)
            assert snap["format"] == "json"
            assert snap["path"] == str(path)
        finally:
            path.unlink(missing_ok=True)

    def test_implements_whole_protocol(self):
        """UT-CONFIG-005: ConfigWriter implements every IConfigReaderProtocol method."""
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.shared.src.contract_config_protocol import IConfigReaderProtocol

        writer = ConfigWriter()
        assert isinstance(writer, IConfigReaderProtocol)
        # Instantiating proves no abstract method is left unimplemented.
        for name in IConfigReaderProtocol.__abstractmethods__:
            assert callable(getattr(writer, name))

    def test_load_file(self):
        """UT-CONFIG-006: load_file returns ConfigTuple with data and format."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"a": 1}')
            f.flush()
            path = Path(f.name)

        try:
            result = writer.load_file(path)
            data, fmt = result
            assert data["a"] == 1
            assert fmt == "json"
        finally:
            path.unlink(missing_ok=True)

    def test_save_file_json(self):
        """UT-CONFIG-007: save_file writes JSON correctly."""
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat

        writer = ConfigWriter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            f.flush()
            path = Path(f.name)

        try:
            data = ConfigData({"key": "value"})
            result = writer.save_file(path, data, ConfigFormat("json"))
            assert result is True
        finally:
            path.unlink(missing_ok=True)

    def test_detect_format_json(self):
        """UT-CONFIG-008: detect_format identifies JSON."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            f.flush()
            path = Path(f.name)

        try:
            result = writer.detect_format(path)
            assert result == "json"
        finally:
            path.unlink(missing_ok=True)

    def test_detect_format_toml(self):
        """UT-CONFIG-009: detect_format identifies TOML."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write('[section]\nkey = "value"')
            f.flush()
            path = Path(f.name)

        try:
            result = writer.detect_format(path)
            assert result == "toml"
        finally:
            path.unlink(missing_ok=True)

    def test_normalize_jsonc(self):
        """UT-CONFIG-010: normalize_jsonc strips comments."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        result = writer.normalize_jsonc('{"key": "value"} // comment')
        assert "//" not in result
        assert '"value"' in result

    def test_dumps_toml(self):
        """UT-CONFIG-011: dumps_toml serializes dict to TOML string."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        data = {"key": "value", "number": 42}
        result = writer.dumps_toml(data)
        assert isinstance(result, str)
        assert "key" in result
        assert "42" in result


class TestConfigModifier:
    """Tests for ConfigModifier capability."""

    def test_init(self):
        """UT-CONFIG-012: ConfigModifier initializes without args."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        assert modifier is not None

    def test_merge_servers_rich_method(self):
        """UT-CONFIG-013: merge_servers() is the named protocol method."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        assert not hasattr(modifier, "execute")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json.dumps({"mcpServers": {}}))
            f.flush()
            path = Path(f.name)

        try:
            result = modifier.merge_servers(path, {"test-server": {"url": "http://test"}})
            assert "test-server" in result
        finally:
            path.unlink(missing_ok=True)

    def test_set_env_rich_method(self):
        """UT-CONFIG-014: set_env() is the named protocol method."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('')
            f.flush()
            path = Path(f.name)

        try:
            modifier.set_env(path, {"KEY": "value"})
            # Verify env file was updated
            content = path.read_text()
            assert 'KEY="value"' in content or "KEY=value" in content
        finally:
            path.unlink(missing_ok=True)

    def test_list_mcp_servers_rich_method(self):
        """UT-CONFIG-015: list_mcp_servers() is the named read method."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json.dumps({"mcpServers": {"a": {}}}))
            f.flush()
            path = Path(f.name)

        try:
            result = modifier.list_mcp_servers(path)
            assert isinstance(result, list)
        finally:
            path.unlink(missing_ok=True)

    def test_implements_whole_protocol(self):
        """UT-CONFIG-016: ConfigModifier implements every IConfigModifierProtocol method."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier
        from modules.shared.src.contract_config_protocol import IConfigModifierProtocol

        modifier = ConfigModifier()
        assert isinstance(modifier, IConfigModifierProtocol)
        for name in IConfigModifierProtocol.__abstractmethods__:
            assert callable(getattr(modifier, name))

    def test_remove_mcp_servers(self):
        """UT-CONFIG-017: remove_mcp_servers returns removed server names."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json.dumps({"mcpServers": {"test-server": {"url": "http://test"}}}))
            f.flush()
            path = Path(f.name)

        try:
            result = modifier.remove_mcp_servers(path, ["test-server"])
            assert "test-server" in result
        finally:
            path.unlink(missing_ok=True)

    def test_remove_env_keys(self):
        """UT-CONFIG-018: remove_env_keys returns removed key names."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("KEY1=value1\nKEY2=value2\n")
            f.flush()
            path = Path(f.name)

        try:
            result = modifier.remove_env_keys(path, ["KEY1"])
            assert "KEY1" in result
            content = path.read_text()
            assert "KEY1" not in content
        finally:
            path.unlink(missing_ok=True)

    def test_list_mcp_servers(self):
        """UT-CONFIG-019: list_mcp_servers returns server names."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json.dumps({"mcpServers": {"server-a": {}, "server-b": {}}}))
            f.flush()
            path = Path(f.name)

        try:
            result = modifier.list_mcp_servers(path)
            assert "server-a" in result
            assert "server-b" in result
        finally:
            path.unlink(missing_ok=True)

    def test_looks_like_env_true(self):
        """UT-CONFIG-020: _looks_like_env returns True for .env files."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        assert modifier._looks_like_env(Path(".env")) is True
        assert modifier._looks_like_env(Path(".env.local")) is True
        assert modifier._looks_like_env(Path("config.env")) is True

    def test_looks_like_env_false(self):
        """UT-CONFIG-021: _looks_like_env returns False for non-env files."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        assert modifier._looks_like_env(Path("config.json")) is False
        assert modifier._looks_like_env(Path("settings.toml")) is False


class TestConfigOrchestrator:
    """Tests for ConfigOrchestrator aggregate."""

    def test_init(self):
        """UT-CONFIG-022: ConfigOrchestrator stores writer and modifier."""
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        writer = ConfigWriter()
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)
        assert orch._writer is writer
        assert orch._modifier is modifier

    def test_execute_load_routes_to_writer(self):
        """UT-CONFIG-023: execute(load) routes to writer.load."""
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier
        from modules.shared.src.taxonomy_common_vo import ConfigOp, ConfigRequest

        writer = MagicMock()
        writer.load.return_value = ({"key": "value"}, "json")
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)

        result = orch.execute(ConfigRequest(ConfigOp("load"), path=Path("/tmp/test.json")))
        assert result.success is True
        assert result.data == ({"key": "value"}, "json")
        writer.load.assert_called_once_with(Path("/tmp/test.json"))

    def test_aggregate_declares_one_method(self):
        """UT-CONFIG-023b: IConfigAggregate declares exactly one method, execute."""
        from modules.shared.src.contract_config_aggregate import IConfigAggregate

        assert IConfigAggregate.__abstractmethods__ == frozenset({"execute"})

    def test_execute_save_routes_to_writer(self):
        """UT-CONFIG-024: execute(save) routes to writer.save."""
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier
        from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat, ConfigOp, ConfigRequest

        writer = MagicMock()
        writer.save.return_value = True
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)

        result = orch.execute(
            ConfigRequest(
                ConfigOp("save"),
                path=Path("/tmp/test.json"),
                data=ConfigData({"key": "value"}),
                fmt=ConfigFormat("json"),
            )
        )
        assert result.success is True
        writer.save.assert_called_once()

    def test_execute_help_returns_usage(self):
        """UT-CONFIG-025: execute(help) returns usage text."""
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_modifier import ConfigModifier
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.shared.src.taxonomy_common_vo import ConfigOp, ConfigRequest
        from modules.shared.src.taxonomy_common_vo import HelpText

        orch = ConfigOrchestrator(ConfigWriter(HelpText("Usage: aa config\n  load PATH\n  save PATH\n")), ConfigModifier())
        result = orch.execute(ConfigRequest(ConfigOp("help")))
        assert result.success is True
        assert "Usage: aa config" in str(result.data)
        assert "load" in str(result.data)
        assert "save" in str(result.data)

    def test_repr(self):
        """UT-CONFIG-026: __repr__ returns descriptive string."""
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        writer = ConfigWriter()
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)
        assert repr(orch) == "ConfigOrchestrator()"


class TestConfigSurface:
    """Tests for ConfigCommand surface adapter."""

    def test_init(self):
        """UT-CONFIG-027: ConfigCommand stores orchestrator reference."""
        from modules.config.src.surface_config_command import ConfigCommand
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        writer = ConfigWriter()
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)
        cmd = ConfigCommand(orch)
        assert cmd._orch is orch

    def test_execute_delegates_to_aggregate(self):
        """UT-CONFIG-028: ConfigCommand.execute delegates to the wrapped aggregate."""
        from modules.config.src.surface_config_command import ConfigCommand
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_modifier import ConfigModifier
        from modules.shared.src.taxonomy_common_vo import ConfigOp, ConfigRequest, ConfigResult

        orch = MagicMock()
        orch.execute.return_value = ConfigResult(True, ({"key": "value"}, "json"))
        cmd = ConfigCommand(orch)

        result = cmd.execute(ConfigRequest(ConfigOp("load"), path=Path("/tmp/test.json")))
        assert result is orch.execute.return_value
        orch.execute.assert_called_once()
        # Named verbs are gone from the surface; only execute remains.
        for gone in ("load", "save", "help"):
            assert not hasattr(cmd, gone)

    def test_help_delegates(self):
        """UT-CONFIG-029: the help op flows through the aggregate's execute."""
        from modules.config.src.surface_config_command import ConfigCommand
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier
        from modules.shared.src.taxonomy_common_vo import ConfigOp, ConfigRequest, HelpText

        cmd = ConfigCommand(ConfigOrchestrator(ConfigWriter(HelpText("Usage: aa config\n  load PATH\n")), ConfigModifier()))
        result = cmd.execute(ConfigRequest(ConfigOp("help")))
        assert result.success is True
        assert "Usage: aa config" in str(result.data)
