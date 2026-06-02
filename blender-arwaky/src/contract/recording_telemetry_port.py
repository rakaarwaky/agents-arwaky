"""
Contract: Port interface for telemetry collection.

Defines the contract for anonymous telemetry recording, configuration, and
decorator utilities. Single port for all telemetry-related concerns.
AES Port layer — depends only on taxonomy entities.
"""

from abc import ABC, abstractmethod

from taxonomy import BlenderVersion, Details, DurationMs, ErrorMessage, EventType, Prompt, SuccessFlag, ToolName


class TelemetryRecordingPort(ABC):
    """Port interface for telemetry collection, configuration, and decorators."""

    @abstractmethod
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
        """Record a telemetry event."""
        pass

    @abstractmethod
    def is_enabled(self) -> SuccessFlag:
        """Check if telemetry is currently enabled."""
        pass

    @abstractmethod
    def create_tool_decorator(self, tool_name: ToolName):
        """Create a decorator that records telemetry for an MCP tool."""
        pass
