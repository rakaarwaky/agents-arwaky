import os
import json
import pytest
import asyncio
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from taxonomy import (
    CustomerUuid, SessionId, Timestamp, VersionString, PlatformName,
    ToolName, Prompt, SuccessFlag, DurationMs, ErrorMessage
)
from taxonomy.telemetry_event_entity import EventType, TelemetryEvent
from infrastructure.telemetry_signal_recorder import (
    TelemetrySignalRecorder,
    _get_package_version,
    record_startup,
)


class TestTelemetryRecorder:
    """Tests for TelemetrySignalRecorder, decorators, and version retrieval."""

    @pytest.fixture
    def mock_conn(self):
        return MagicMock()

    @pytest.fixture
    def mock_config(self):
        cfg = MagicMock()
        cfg.enabled = True
        cfg.data_dir = None
        cfg.max_prompt_length = 50
        return cfg

    def test_get_package_version(self):
        # Fallback when importlib fails
        with patch("importlib.metadata.version", side_effect=ImportError()):
            # pyproject.toml exists mock
            with patch.object(Path, "exists", return_value=True):
                # mock safe_load
                with patch("builtins.open", mock_open(read_data=b"project:\n  version: 2.0.0\n")):
                    with patch("infrastructure.telemetry_signal_recorder._toml_parser") as mock_parser:
                        mock_parser.load.return_value = {"project": {"version": "2.0.0"}}
                        assert _get_package_version() == "2.0.0"

        # Failure fallback
        with patch("importlib.metadata.version", side_effect=ImportError()):
            with patch.object(Path, "exists", return_value=False):
                assert _get_package_version() == "unknown"

    def test_record_startup(self):
        # Best effort startup logging
        record_startup()

    def test_telemetry_initialize_data_dir(self, mock_conn, mock_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.data_dir = tmpdir
            recorder = TelemetrySignalRecorder(mock_conn, mock_config)
            assert recorder.is_enabled() is True
            assert Path(tmpdir).exists()
            assert recorder._jsonl_path == Path(tmpdir) / "telemetry.jsonl"

    def test_telemetry_get_data_directory_platforms(self, mock_conn, mock_config):
        # Windows APPDATA path
        with patch("sys.platform", "win32"):
            with patch.dict(os.environ, {"APPDATA": "/mock/appdata"}):
                recorder = TelemetrySignalRecorder(mock_conn, mock_config)
                assert "/mock/appdata" in str(recorder._get_data_directory())

        # Darwin path
        with patch("sys.platform", "darwin"):
            recorder = TelemetrySignalRecorder(mock_conn, mock_config)
            assert "Library/Application Support" in str(recorder._get_data_directory())

        # Linux XDG path
        with patch("sys.platform", "linux"):
            with patch.dict(os.environ, {"XDG_DATA_HOME": "/mock/xdg"}):
                recorder = TelemetrySignalRecorder(mock_conn, mock_config)
                assert "/mock/xdg" in str(recorder._get_data_directory())

    def test_get_or_create_uuid_read_existing(self, mock_conn, mock_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.data_dir = tmpdir
            # Write existing
            uuid_file = Path(tmpdir) / "customer_uuid.txt"
            uuid_file.write_text("existing-uuid-123", encoding="utf-8")

            recorder = TelemetrySignalRecorder(mock_conn, mock_config)
            assert recorder._customer_uuid == "existing-uuid-123"

    def test_get_or_create_uuid_creation_error_fallback(self, mock_conn, mock_config):
        with patch.object(Path, "mkdir", side_effect=Exception("Write protected")):
            recorder = TelemetrySignalRecorder(mock_conn, mock_config)
            # Falls back to random uuid without crashing
            assert recorder._customer_uuid is not None

    def test_check_user_consent(self, mock_conn, mock_config):
        recorder = TelemetrySignalRecorder(mock_conn, mock_config)
        # Success path
        mock_conn.send_command.return_value = {"consent": True}
        assert recorder._check_user_consent() is True
        # Caching check works
        assert recorder._check_user_consent() is True

        # Remote call exception falls back to False
        recorder._consent_cache = None
        mock_conn.send_command.side_effect = Exception("Blender offline")
        assert recorder._check_user_consent() is False

    def test_record_event_disabled_no_op(self, mock_conn, mock_config):
        mock_config.enabled = False
        recorder = TelemetrySignalRecorder(mock_conn, mock_config)
        recorder.record_event(EventType.TOOL_EXECUTION)
        assert recorder._queue.qsize() == 0

    def test_record_event_consent_withheld(self, mock_conn, mock_config):
        recorder = TelemetrySignalRecorder(mock_conn, mock_config)
        # Mock consent withheld
        with patch.object(recorder, "_check_user_consent", return_value=False):
            recorder.record_event(
                EventType.TOOL_EXECUTION,
                prompt_text=Prompt("secrets"),
                error_message=ErrorMessage("Critical password leak detail"),
                metadata={"secret": 123}
            )
            # Queue should contain event with prompt/metadata stripped, error sanitized
            event = recorder._queue.get()
            assert event.prompt_text is None
            assert event.metadata is None
            assert "withheld" in event.error_message

    def test_record_event_truncations(self, mock_conn, mock_config):
        recorder = TelemetrySignalRecorder(mock_conn, mock_config)
        # Consent granted
        with patch.object(recorder, "_check_user_consent", return_value=True):
            # Prompt longer than 50
            long_prompt = "a" * 100
            # Error message longer than 200
            long_error = "e" * 300
            recorder.record_event(
                EventType.TOOL_EXECUTION,
                prompt_text=Prompt(long_prompt),
                error_message=ErrorMessage(long_error),
            )
            event = recorder._queue.get()
            assert len(event.prompt_text) <= 53  # 50 + "..."
            assert event.prompt_text.endswith("...")
            assert len(event.error_message) <= 203  # 200 + "..."

    def test_record_event_queue_full(self, mock_conn, mock_config):
        recorder = TelemetrySignalRecorder(mock_conn, mock_config)
        # Fill queue
        recorder._queue.maxsize = 1
        recorder._queue.put_nowait(TelemetryEvent(
            event_type=EventType.TOOL_EXECUTION,
            customer_uuid=CustomerUuid("1"),
            session_id=SessionId("1"),
            timestamp=Timestamp(1.0),
            version=VersionString("1"),
            platform=PlatformName("linux"),
        ))
        # This shouldn't crash when full
        recorder.record_event(EventType.TOOL_EXECUTION)

    def test_worker_loop_and_send_event(self, mock_conn, mock_config):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.data_dir = tmpdir
            recorder = TelemetrySignalRecorder(mock_conn, mock_config)

            event = TelemetryEvent(
                event_type=EventType.TOOL_EXECUTION,
                customer_uuid=CustomerUuid("cust-99"),
                session_id=SessionId("sess-99"),
                timestamp=Timestamp(123456),
                version=VersionString("1.0"),
                platform=PlatformName("linux"),
                tool_name=ToolName("test_tool"),
                prompt_text=Prompt("draw sphere"),
                success=SuccessFlag(True),
                duration_ms=DurationMs(150.0),
                error_message=None,
            )
            # Write to jsonl
            recorder._send_event(event)
            # Check contents
            assert recorder._jsonl_path.exists()
            lines = recorder._jsonl_path.read_text(encoding="utf-8").splitlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["customer_uuid"] == "cust-99"
            assert data["tool_name"] == "test_tool"
            assert data["duration_ms"] == 150.0

            # File write exception safety
            with patch("builtins.open", side_effect=Exception("Disk full")):
                recorder._send_event(event)  # Safe, doesn't raise

    @pytest.mark.asyncio
    async def test_create_tool_decorator_sync(self, mock_conn, mock_config):
        recorder = TelemetrySignalRecorder(mock_conn, mock_config)
        # Mock consent check to speed up
        with patch.object(recorder, "_check_user_consent", return_value=True):
            decorator = recorder.create_tool_decorator(ToolName("my_sync_tool"))

            # Sync success
            @decorator
            def sync_tool(x, y):
                return x + y

            res = sync_tool(2, 3)
            assert res == 5
            # Event should be queued
            event = recorder._queue.get()
            assert event.tool_name == "my_sync_tool"
            assert event.success is True

            # Sync failure
            @decorator
            def sync_tool_fail():
                raise ValueError("Calculus mismatch")

            with pytest.raises(ValueError):
                sync_tool_fail()
            event2 = recorder._queue.get()
            assert event2.success is False
            assert "Calculus mismatch" in event2.error_message

    @pytest.mark.asyncio
    async def test_create_tool_decorator_async(self, mock_conn, mock_config):
        recorder = TelemetrySignalRecorder(mock_conn, mock_config)
        with patch.object(recorder, "_check_user_consent", return_value=True):
            decorator = recorder.create_tool_decorator(ToolName("my_async_tool"))

            # Async success
            @decorator
            async def async_tool(x):
                await asyncio.sleep(0.001)
                return x * 10

            res = await async_tool(5)
            assert res == 50
            event = recorder._queue.get()
            assert event.tool_name == "my_async_tool"
            assert event.success is True

            # Async failure
            @decorator
            async def async_tool_fail():
                await asyncio.sleep(0.001)
                raise RuntimeError("Network reset")

            with pytest.raises(RuntimeError):
                await async_tool_fail()
            event2 = recorder._queue.get()
            assert event2.success is False
            assert "Network reset" in event2.error_message
