"""
Telemetry convenience API: global accessors and shorthand functions.

Import functions from here to record common telemetry events.
Communicates solely via contract ports (ConfigPort, TelemetryRecordingPort).
"""

from typing import Optional

from contract import ConfigPort, TelemetryRecordingPort
from taxonomy import BlenderVersion, Details, DurationMs, ErrorMessage, EventType, Prompt, SuccessFlag, ToolName

# ─── Global singleton for backward compat ─────────────────────────────────────

_telemetry_api: Optional["TelemetryApi"] = None


class TelemetryApi(TelemetryRecordingPort):
    """AES-compliant facade: groups telemetry convenience functions.

    Accepts ConfigPort and TelemetryRecordingPort via constructor injection.
    All telemetry calls are forwarded to the injected recorder port.
    """

    def __init__(
        self,
        recorder_port: TelemetryRecordingPort,
        config_port: ConfigPort | None = None,
    ) -> None:
        self._recorder = recorder_port
        self._config = config_port

    # ─── Convenience methods ─────────────────────────────────────────────────

    def record_tool_usage(
        self,
        tool_name: str,
        success: bool,
        duration_ms: float,
        error: str | None = None,
    ):
        """Record a tool execution event."""
        self._recorder.record_event(
            event_type=EventType.TOOL_EXECUTION,
            tool_name=ToolName(tool_name),
            success=SuccessFlag(success),
            duration_ms=DurationMs(duration_ms),
            error_message=ErrorMessage(error) if error else None,
        )

    def record_startup(self, blender_version: str | None = None):
        """Record server startup event."""
        self._recorder.record_event(
            event_type=EventType.STARTUP,
            success=SuccessFlag(True),
            blender_version=BlenderVersion(blender_version) if blender_version else None,
        )

    def is_telemetry_enabled(self) -> bool:
        """Check if telemetry is enabled."""
        return bool(self._recorder.is_enabled())

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
        return self._recorder.create_tool_decorator(tool_name)

    # ─── Module-level initialisation ─────────────────────────────────────────

    @staticmethod
    def initialize(recorder_port: TelemetryRecordingPort) -> "TelemetryApi":
        """Set the global singleton. Called from DI container."""
        global _telemetry_api
        _telemetry_api = TelemetryApi(recorder_port=recorder_port)
        return _telemetry_api


# ─── Module-level aliases (backward compat) ──────────────────────────────────


def record_tool_usage(
    tool_name: str,
    success: bool,
    duration_ms: float,
    error: str | None = None,
):
    """Backward-compat: forward to global TelemetryApi singleton."""
    if _telemetry_api is None:
        return
    _telemetry_api.record_tool_usage(tool_name, success, duration_ms, error)


def record_startup(blender_version: str | None = None):
    """Backward-compat: forward to global TelemetryApi singleton."""
    if _telemetry_api is None:
        return
    _telemetry_api.record_startup(blender_version)


def is_telemetry_enabled() -> bool:
    """Backward-compat: check if telemetry is enabled."""
    if _telemetry_api is None:
        return False
    return _telemetry_api.is_telemetry_enabled()
