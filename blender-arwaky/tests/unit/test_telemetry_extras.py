"""Unit tests for telemetry utility extras, decorators, and configurations."""
import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from taxonomy import (
    EventType, ToolName, SuccessFlag, DurationMs, ErrorMessage,
    BlenderVersion
)
from infrastructure.telemetry_config_loader import TelemetryConfig
from infrastructure.telemetry_api_util import (
    TelemetryApi,
    record_tool_usage,
    record_startup,
    is_telemetry_enabled,
)
from infrastructure.telemetry_decorator_adapter import TelemetryDecoratorAdapter


class TestTelemetryConfigLoader:
    """Tests for TelemetryConfig loader and overrides."""

    def test_telemetry_config_env_disable(self):
        # 1. DISABLE_TELEMETRY = true
        with patch.dict(os.environ, {"DISABLE_TELEMETRY": "true"}):
            config = TelemetryConfig()
            assert config.is_enabled() is False

        # 2. BLENDER_MCP_DISABLE_TELEMETRY = true
        with patch.dict(os.environ, {"BLENDER_MCP_DISABLE_TELEMETRY": "TRUE"}):
            config = TelemetryConfig()
            assert config.is_enabled() is False

    def test_telemetry_config_yaml(self):
        # telemetry.enabled = True in yaml
        with patch.dict(os.environ, {}, clear=True):
            with patch("infrastructure.config_file_loader.ApplicationConfigLoader.get_config", return_value=True):
                config = TelemetryConfig()
                assert config.is_enabled() is True

            # telemetry.enabled = False in yaml
            with patch("infrastructure.config_file_loader.ApplicationConfigLoader.get_config", return_value=False):
                config = TelemetryConfig()
                assert config.is_enabled() is False

            # telemetry.enabled is None (not set)
            with patch("infrastructure.config_file_loader.ApplicationConfigLoader.get_config", return_value=None):
                config = TelemetryConfig()
                assert config.is_enabled() is False

    def test_telemetry_config_get_methods(self):
        config = TelemetryConfig()
        assert config.get("enabled") == config.enabled
        assert config.get("max_prompt_length") == 500
        assert config.get("nonexistent_path", "default_val") == "default_val"


class TestTelemetryApiUtil:
    """Tests for TelemetryApi facades and global helpers."""

    @pytest.fixture(autouse=True)
    def reset_global_singleton(self):
        import infrastructure.telemetry_api_util as tau
        old_singleton = tau._telemetry_api
        tau._telemetry_api = None
        yield
        tau._telemetry_api = old_singleton

    def test_telemetry_api_methods(self):
        mock_recorder = MagicMock()
        mock_recorder.is_enabled.return_value = SuccessFlag(True)
        api = TelemetryApi(recorder_port=mock_recorder)

        # 1. record_tool_usage
        api.record_tool_usage("draw_box", True, 250.0, "No error")
        mock_recorder.record_event.assert_called_with(
            event_type=EventType.TOOL_EXECUTION,
            tool_name=ToolName("draw_box"),
            success=SuccessFlag(True),
            duration_ms=DurationMs(250.0),
            error_message=ErrorMessage("No error"),
        )

        # 2. record_startup
        api.record_startup("3.6.0")
        mock_recorder.record_event.assert_called_with(
            event_type=EventType.STARTUP,
            success=SuccessFlag(True),
            blender_version=BlenderVersion("3.6.0"),
        )

        # 3. record_event direct delegation
        api.record_event(EventType.TOOL_EXECUTION, tool_name=ToolName("foo"))
        mock_recorder.record_event.assert_called_with(
            event_type=EventType.TOOL_EXECUTION,
            tool_name=ToolName("foo"),
            prompt_text=None,
            success=SuccessFlag(True),
            duration_ms=None,
            error_message=None,
            blender_version=None,
            metadata=None,
        )

        # 4. is_enabled, is_telemetry_enabled, and create_tool_decorator
        assert api.is_telemetry_enabled() is True
        assert api.is_enabled() is True
        api.create_tool_decorator(ToolName("my_tool"))
        mock_recorder.create_tool_decorator.assert_called_with(ToolName("my_tool"))

    def test_global_shorthand_aliases(self):
        mock_recorder = MagicMock()
        mock_recorder.is_enabled.return_value = SuccessFlag(True)

        # Before initialize, they should be no-ops or return False
        assert is_telemetry_enabled() is False
        record_tool_usage("foo", True, 1.0)  # doesn't crash
        record_startup()  # doesn't crash

        # Initialize
        TelemetryApi.initialize(mock_recorder)

        # Now they should delegate to the singleton
        assert is_telemetry_enabled() is True

        record_tool_usage("foo", True, 50.0)
        mock_recorder.record_event.assert_called_with(
            event_type=EventType.TOOL_EXECUTION,
            tool_name=ToolName("foo"),
            success=SuccessFlag(True),
            duration_ms=DurationMs(50.0),
            error_message=None,
        )

        record_startup("4.0.0")
        mock_recorder.record_event.assert_called_with(
            event_type=EventType.STARTUP,
            success=SuccessFlag(True),
            blender_version=BlenderVersion("4.0.0"),
        )


class TestTelemetryDecoratorAdapter:
    """Tests for TelemetryDecoratorAdapter sync and async functionality."""

    @pytest.mark.asyncio
    async def test_decorator_sync_usage(self):
        mock_recorder = MagicMock()
        decorator_adapter = TelemetryDecoratorAdapter(mock_recorder)

        @decorator_adapter.telemetry_tool(ToolName("sync_decorated"))
        def my_sync_fn(x, y):
            if x < 0:
                raise ValueError("x must be positive")
            return x + y

        # Success path
        res = my_sync_fn(10, 20)
        assert res == 30
        mock_recorder.record_event.assert_called_once()
        args, kwargs = mock_recorder.record_event.call_args
        assert kwargs["event_type"] == EventType.TOOL_EXECUTION
        assert kwargs["tool_name"] == ToolName("sync_decorated")
        assert kwargs["success"] is True
        assert kwargs["error_message"] is None

        # Failure path
        mock_recorder.record_event.reset_mock()
        with pytest.raises(ValueError):
            my_sync_fn(-5, 10)
        mock_recorder.record_event.assert_called_once()
        args, kwargs = mock_recorder.record_event.call_args
        assert kwargs["success"] is False
        assert "x must be positive" in str(kwargs["error_message"])

    @pytest.mark.asyncio
    async def test_decorator_async_usage(self):
        mock_recorder = MagicMock()
        decorator_adapter = TelemetryDecoratorAdapter(mock_recorder)

        @decorator_adapter.create_tool_decorator(ToolName("async_decorated"))
        async def my_async_fn(x):
            await asyncio.sleep(0.001)
            if x == 0:
                raise ZeroDivisionError("division by zero")
            return 100 / x

        # Success path
        res = await my_async_fn(2)
        assert res == 50
        mock_recorder.record_event.assert_called_once()
        args, kwargs = mock_recorder.record_event.call_args
        assert kwargs["success"] is True

        # Failure path
        mock_recorder.record_event.reset_mock()
        with pytest.raises(ZeroDivisionError):
            await my_async_fn(0)
        mock_recorder.record_event.assert_called_once()
        args, kwargs = mock_recorder.record_event.call_args
        assert kwargs["success"] is False
        assert "division by zero" in str(kwargs["error_message"])

    def test_decorator_exception_safety(self):
        # Even if recorder fails, decorator shouldn't crash the decorated function
        mock_recorder = MagicMock()
        mock_recorder.record_event.side_effect = Exception("Disk full")
        decorator_adapter = TelemetryDecoratorAdapter(mock_recorder)

        @decorator_adapter.telemetry_tool(ToolName("sync_decorated"))
        def safe_fn():
            return 42

        assert safe_fn() == 42  # works!

    def test_delegated_methods(self):
        mock_recorder = MagicMock()
        mock_recorder.is_enabled.return_value = SuccessFlag(True)
        decorator_adapter = TelemetryDecoratorAdapter(mock_recorder)

        assert decorator_adapter.is_enabled() is True

        decorator_adapter.record_event(EventType.STARTUP, blender_version=BlenderVersion("3.0"))
        mock_recorder.record_event.assert_called_with(
            event_type=EventType.STARTUP,
            tool_name=None,
            prompt_text=None,
            success=SuccessFlag(True),
            duration_ms=None,
            error_message=None,
            blender_version=BlenderVersion("3.0"),
            metadata=None,
        )
