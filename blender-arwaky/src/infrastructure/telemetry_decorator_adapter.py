"""
Telemetry decorator for Blender MCP tools.

Depends only on contract TelemetryRecordingPort, not on concrete infra modules.
"""

import functools
import inspect
import logging
import time
from collections.abc import Callable
from typing import Any

from contract import TelemetryRecordingPort
from taxonomy import BlenderVersion, Details, DurationMs, ErrorMessage, EventType, Prompt, SuccessFlag, ToolName

logger = logging.getLogger("blender-mcp-telemetry_service")


class TelemetryDecoratorAdapter(TelemetryRecordingPort):
    """Wrapper class for telemetry tool decorator.

    Accepts a TelemetryRecordingPort via constructor to forward events.
    """

    def __init__(self, recorder: TelemetryRecordingPort) -> None:
        self._recorder = recorder

    def _record_usage(
        self,
        tool_name: ToolName,
        success: SuccessFlag,
        duration_ms: DurationMs,
        error: ErrorMessage | None = None,
    ) -> None:
        """Record tool usage via injected recorder port."""
        try:
            self._recorder.record_event(
                event_type=EventType.TOOL_EXECUTION,
                tool_name=tool_name,
                success=success,
                duration_ms=duration_ms,
                error_message=error,
            )
        except Exception as log_error:  # pragma: no cover
            logger.debug(f"Failed to record telemetry: {log_error}")  # pragma: no cover

    @staticmethod
    def _build_decorator(recorder: TelemetryRecordingPort, tool_name: ToolName) -> Callable:
        """Build a decorator that records telemetry using the given recorder."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                success = False
                error = None

                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    error = str(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    try:
                        recorder.record_event(
                            event_type=EventType.TOOL_EXECUTION,
                            tool_name=tool_name,
                            success=SuccessFlag(success),
                            duration_ms=DurationMs(duration_ms),
                            error_message=ErrorMessage(error) if error else None,
                        )
                    except Exception as log_error:
                        logger.debug(f"Failed to record telemetry: {log_error}")

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                success = False
                error = None

                try:
                    result = await func(*args, **kwargs)
                    success = True
                    return result
                except Exception as e:
                    error = str(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    try:
                        recorder.record_event(
                            event_type=EventType.TOOL_EXECUTION,
                            tool_name=tool_name,
                            success=SuccessFlag(success),
                            duration_ms=DurationMs(duration_ms),
                            error_message=ErrorMessage(error) if error else None,
                        )
                    except Exception as log_error:
                        logger.debug(f"Failed to record telemetry: {log_error}")

            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def telemetry_tool(self, tool_name: ToolName) -> Callable:
        """Create a decorator that records telemetry for an MCP tool."""
        decorator: Callable = self._build_decorator(self._recorder, tool_name)
        return decorator

    # ─── TelemetryRecordingPort implementations ──────────────────────────────

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
        self._recorder.record_event(
            event_type=event_type,
            tool_name=tool_name,
            prompt_text=prompt_text,
            success=success if success is not None else SuccessFlag(True),
            duration_ms=duration_ms,
            error_message=error_message,
            blender_version=blender_version,
            metadata=metadata,
        )

    def is_enabled(self) -> SuccessFlag:
        return self._recorder.is_enabled()

    def create_tool_decorator(self, tool_name: ToolName):
        return self.telemetry_tool(tool_name)
