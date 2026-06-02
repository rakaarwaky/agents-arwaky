"""
Privacy-focused, anonymous telemetry collection for Blender MCP.
Includes module-level version utilities and initialization helpers.
"""

import asyncio
import contextlib
import json
import logging
import os
import platform
import queue
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from contract import BlenderConnectionPort, TelemetryRecordingPort
from taxonomy import (
    ActionName,
    BlenderVersion,
    CustomerUuid,
    Details,
    DurationMs,
    ErrorMessage,
    PlatformName,
    Prompt,
    SessionId,
    SuccessFlag,
    Timestamp,
    ToolName,
    VersionString,
)
from taxonomy.telemetry_event_entity import EventType, TelemetryEvent

logger = logging.getLogger("blender-mcp-telemetry-service")

# ─── TOML parser (stdlib in 3.11+, fallback to tomli) ────
_toml_parser: Any = None
try:
    import tomli as _tomli

    _toml_parser = _tomli
except ImportError:  # pragma: no cover
    try:  # pragma: no cover
        import tomllib as _tomllib  # pragma: no cover

        _toml_parser = _tomllib  # pragma: no cover
    except ImportError:  # pragma: no cover
        pass  # pragma: no cover


def _get_package_version() -> str:
    """Get package version from importlib metadata (works for pip-installed packages)."""
    try:
        from importlib.metadata import version as _v

        return _v("blender-mcp")
    except Exception:  # nosec B110 — import fallback, safe to skip
        pass
    # Fallback: try pyproject.toml in dev layout
    try:
        p = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        if p.exists() and _toml_parser:
            with open(p, "rb") as f:
                v = _toml_parser.load(f).get("project", {}).get("version", "unknown")
                return str(v)
    except Exception:  # pragma: no cover
        logger.debug("Failed to read package version")  # pragma: no cover
    return "unknown"


MCP_VERSION = _get_package_version()


def record_startup() -> None:
    """Record startup event — best effort, never raises."""
    logger.debug("Startup telemetry recorded (module-level no-op)")


class TelemetrySignalRecorder(TelemetryRecordingPort):
    """Main telemetry collection class"""

    def __init__(self, connection: BlenderConnectionPort, config: Any) -> None:
        self._connection = connection
        self.config_application = config
        self._customer_uuid: CustomerUuid = CustomerUuid(self._get_or_create_uuid())
        self._session_id: SessionId = SessionId(str(uuid.uuid4()))
        self._event_timestamps: list[float] = []
        self._rate_limit_lock = threading.Lock()
        self._consent_cache: bool | None = None
        self._last_consent_check: float = 0
        self._consent_check_interval: float = 300
        self._queue: queue.Queue[TelemetryEvent] = queue.Queue(maxsize=1000)
        self._worker: threading.Thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()
        self._data_dir = self._get_data_directory()
        self._jsonl_path = self._data_dir / "telemetry.jsonl"
        logger.info(
            "Telemetry initialized (enabled=%s, path=%s, customer_uuid=%s)",
            self.config_application.enabled,
            self._jsonl_path,
            self._customer_uuid,
        )

    def is_enabled(self) -> SuccessFlag:
        return SuccessFlag(self.config_application.enabled)

    def create_tool_decorator(self, tool_name: ToolName):
        import functools
        from collections.abc import Callable

        def _build(func: Callable) -> Callable:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                start = time.time()
                success, err = False, None
                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    err = str(e)
                    raise
                finally:
                    with contextlib.suppress(Exception):
                        self.record_event(
                            event_type=EventType.TOOL_EXECUTION,
                            tool_name=tool_name,
                            success=SuccessFlag(success),
                            duration_ms=DurationMs((time.time() - start) * 1000),
                            error_message=ErrorMessage(err) if err is not None else None,
                        )

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                start = time.time()
                success, err = False, None
                try:
                    result = await func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    err = str(e)
                    raise
                finally:
                    with contextlib.suppress(Exception):
                        self.record_event(
                            event_type=EventType.TOOL_EXECUTION,
                            tool_name=tool_name,
                            success=SuccessFlag(success),
                            duration_ms=DurationMs((time.time() - start) * 1000),
                            error_message=ErrorMessage(err) if err is not None else None,
                        )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return _build

    def _get_data_directory(self) -> Path:
        with contextlib.suppress(Exception):
            config_dir = getattr(self.config_application, "data_dir", None)
            if config_dir:
                data_dir = Path(config_dir)
                data_dir.mkdir(parents=True, exist_ok=True)
                return data_dir
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        d = base / "BlenderMCP"
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.debug(f"Failed to create data directory {d}: {e}")
        return d

    def _get_or_create_uuid(self) -> str:
        try:
            data_dir = self._get_data_directory()
            uuid_file = data_dir / "customer_uuid.txt"
            if uuid_file.exists():
                uid = uuid_file.read_text(encoding="utf-8").strip()
                if uid:
                    return uid
            uid = str(uuid.uuid4())
            uuid_file.write_text(uid, encoding="utf-8")
            if sys.platform != "win32":
                os.chmod(uuid_file, 0o600)
            return uid
        except Exception as e:
            logger.debug(f"Failed to persist UUID: {e}")
            return str(uuid.uuid4())

    def _check_user_consent(self) -> bool:
        now = time.time()
        if self._consent_cache is not None and (now - self._last_consent_check < self._consent_check_interval):
            return self._consent_cache
        try:
            result = self._connection.send_command(ActionName("get_telemetry_consent"), {})
            consent = result.get("consent", False)
            self._consent_cache = consent
            self._last_consent_check = now
            return bool(consent)
        except Exception:
            return False

    def record_event(
        self,
        event_type: EventType,
        tool_name: ToolName | None = None,
        prompt_text: Prompt | None = None,
        success: SuccessFlag | None = None,
        duration_ms: DurationMs | None = None,
        error_message: ErrorMessage | None = None,
        blender_version: BlenderVersion | None = None,
        metadata: Details | None = None,
    ):
        success = success if success is not None else SuccessFlag(True)
        if not self.config_application.enabled:
            return
        user_consent = self._check_user_consent()
        if not user_consent:
            prompt_text = None
            metadata = None
            if error_message:
                error_message = ErrorMessage("Error occurred (details withheld)")
        if prompt_text and len(prompt_text) > self.config_application.max_prompt_length:
            prompt_text = Prompt(prompt_text[: self.config_application.max_prompt_length] + "...")
        if error_message and user_consent and len(error_message) > 200:
            error_message = ErrorMessage(error_message[:200] + "...")
        event = TelemetryEvent(
            event_type=event_type,
            customer_uuid=self._customer_uuid,
            session_id=self._session_id,
            timestamp=Timestamp(time.time()),
            version=VersionString(MCP_VERSION),
            platform=PlatformName(platform.system().lower()),
            tool_name=tool_name,
            prompt_text=prompt_text,
            success=success,
            duration_ms=duration_ms,
            error_message=error_message,
            blender_version=blender_version,
            metadata=metadata,
        )
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            logger.debug("Telemetry queue full, dropping event")

    def _worker_loop(self):
        while True:
            event = self._queue.get()
            try:
                self._send_event(event)
            except Exception as e:
                logger.debug(f"Telemetry send failed: {e}")
            finally:
                with contextlib.suppress(Exception):
                    self._queue.task_done()

    def _send_event(self, event: TelemetryEvent):
        """Write a telemetry event as one JSON line to the local JSONL file."""
        try:
            data = {
                "customer_uuid": event.customer_uuid,
                "session_id": event.session_id,
                "event_type": event.event_type.value,
                "tool_name": event.tool_name,
                "prompt_text": event.prompt_text,
                "success": event.success,
                "duration_ms": event.duration_ms,
                "error_message": event.error_message,
                "version": event.version,
                "platform": event.platform,
                "blender_version": event.blender_version,
                "metadata": event.metadata or {},
                "event_timestamp": int(event.timestamp),
            }
            line = json.dumps(data, ensure_ascii=False, default=str)
            with open(self._jsonl_path, "a", encoding="utf-8") as f:
                f.write(line)
                f.write("\n")
        except Exception as e:
            logger.debug("Failed to write telemetry event: %s", e)
