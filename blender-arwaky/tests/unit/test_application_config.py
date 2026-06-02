"""Tests for application configuration module."""
import pytest
from infrastructure.config_file_loader import get_config


class TestApplicationConfig:
    """Tests for get_config() with defaults."""

    def test_get_config_returns_default_for_unknown_key(self):
        """get_config should return default for unknown keys."""
        result = get_config("nonexistent.key", "fallback")
        assert result == "fallback"

    def test_get_config_returns_none_for_missing_key(self):
        """get_config should return None when no default and key missing."""
        result = get_config("completely.missing.key")
        assert result is None

    def test_get_config_blender_host_default(self):
        """Default blender.host should be 'localhost'."""
        host = get_config("blender.host", "localhost")
        assert host == "localhost"

    def test_get_config_blender_port_default(self):
        """Default blender.port should be 9876."""
        port = get_config("blender.port", 9876)
        assert port == 9876

    def test_get_config_server_transport_default(self):
        """Default server.transport should be 'stdio'."""
        transport = get_config("server.transport", "stdio")
        assert transport == "stdio"

    def test_get_config_root_level(self):
        """get_config should work with single-level keys."""
        value = get_config("hunyuan", None)
        # Should not crash — returns None or a dict
        assert value is None or isinstance(value, dict)
