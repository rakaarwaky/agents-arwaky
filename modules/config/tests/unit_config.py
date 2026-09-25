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

    def test_execute_load_op(self):
        """UT-CONFIG-002: execute('load') dispatches to load_file."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"key": "value"}')
            f.flush()
            path = Path(f.name)

        try:
            result = writer.execute("load", path)
            data, fmt = result
            assert data["key"] == "value"
            assert fmt == "json"
        finally:
            path.unlink(missing_ok=True)

    def test_execute_save_op(self):
        """UT-CONFIG-003: execute('save') dispatches to save_file."""
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat

        writer = ConfigWriter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            f.flush()
            path = Path(f.name)

        try:
            data = ConfigData({"new_key": "new_value"})
            fmt = ConfigFormat("json")
            result = writer.execute("save", path, {"data": dict(data), "fmt": fmt})
            assert result is True
        finally:
            path.unlink(missing_ok=True)

    def test_execute_detect_format_op(self):
        """UT-CONFIG-004: execute('detect_format') dispatches to detect_format."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            f.flush()
            path = Path(f.name)

        try:
            result = writer.execute("detect_format", path)
            assert result == "json"
        finally:
            path.unlink(missing_ok=True)

    def test_execute_invalid_op_raises(self):
        """UT-CONFIG-005: execute raises ValueError for unknown op."""
        from modules.config.src.capabilities_config_writer import ConfigWriter

        writer = ConfigWriter()
        try:
            writer.execute("unknown_op", Path("/tmp/test.json"))
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "unknown_op" in str(exc)

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

    def test_execute_merge_servers_op(self):
        """UT-CONFIG-013: execute('merge_servers') dispatches correctly."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json.dumps({"mcpServers": {}}))
            f.flush()
            path = Path(f.name)

        try:
            servers = {"test-server": {"url": "http://test"}}
            result = modifier.execute("merge_servers", path, {"servers": servers})
            assert isinstance(result, list)
        finally:
            path.unlink(missing_ok=True)

    def test_execute_set_env_op(self):
        """UT-CONFIG-014: execute('set_env') dispatches correctly."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write('')
            f.flush()
            path = Path(f.name)

        try:
            modifier.execute("set_env", path, {"pairs": {"KEY": "value"}})
            # Verify env file was updated
            content = path.read_text()
            assert 'KEY="value"' in content or "KEY=value" in content
        finally:
            path.unlink(missing_ok=True)

    def test_execute_list_servers_op(self):
        """UT-CONFIG-015: execute('list_servers') dispatches correctly."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            f.flush()
            path = Path(f.name)

        try:
            result = modifier.execute("list_servers", path)
            assert isinstance(result, list)
        finally:
            path.unlink(missing_ok=True)

    def test_execute_invalid_op_raises(self):
        """UT-CONFIG-016: execute raises ValueError for unknown op."""
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        modifier = ConfigModifier()
        try:
            modifier.execute("unknown", Path("/tmp/test.json"))
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "unknown" in str(exc)

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

    def test_load(self):
        """UT-CONFIG-023: load delegates to writer.execute('load')."""
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        writer = MagicMock()
        writer.execute.return_value = ({"key": "value"}, "json")
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)

        result = orch.load(Path("/tmp/test.json"))
        assert result == ({"key": "value"}, "json")
        writer.execute.assert_called_once_with("load", Path("/tmp/test.json"))

    def test_save(self):
        """UT-CONFIG-024: save delegates to writer.execute('save')."""
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier
        from modules.shared.src.taxonomy_common_vo import ConfigData, ConfigFormat

        writer = MagicMock()
        writer.execute.return_value = True
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)

        result = orch.save(Path("/tmp/test.json"), ConfigData({"key": "value"}), ConfigFormat("json"))
        assert result is True
        writer.execute.assert_called_once()
        call_args = writer.execute.call_args
        assert call_args[0][0] == "save"

    def test_help(self):
        """UT-CONFIG-025: help returns usage text."""
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        writer = ConfigWriter()
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)

        result = orch.help()
        assert "Usage: aa config" in str(result)
        assert "load" in str(result)
        assert "save" in str(result)

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

    def test_load_delegates(self):
        """UT-CONFIG-028: ConfigCommand.load delegates to orchestrator."""
        from modules.config.src.surface_config_command import ConfigCommand
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        writer = MagicMock()
        writer.execute.return_value = ({"key": "value"}, "json")
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)
        cmd = ConfigCommand(orch)

        result = cmd.load(Path("/tmp/test.json"))
        assert result == ({"key": "value"}, "json")

    def test_help_delegates(self):
        """UT-CONFIG-029: ConfigCommand.help delegates to orchestrator."""
        from modules.config.src.surface_config_command import ConfigCommand
        from modules.config.src.agent_config_orchestrator import ConfigOrchestrator
        from modules.config.src.capabilities_config_writer import ConfigWriter
        from modules.config.src.capabilities_config_modifier import ConfigModifier

        writer = ConfigWriter()
        modifier = ConfigModifier()
        orch = ConfigOrchestrator(writer, modifier)
        cmd = ConfigCommand(orch)

        result = cmd.help()
        assert "Usage: aa config" in str(result)
