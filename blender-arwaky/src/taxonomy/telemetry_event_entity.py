"""Telemetry event types and data structures."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from taxonomy.core_types_vo import (
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


class EventType(Enum):
    """Types of telemetry events"""

    STARTUP = "startup"
    TOOL_EXECUTION = "tool_execution"
    PROMPT_SENT = "prompt_sent"
    CONNECTION = "connection"
    ERROR = "error"


@dataclass
class TelemetryEvent:
    """Structure for telemetry events"""

    event_type: EventType
    customer_uuid: CustomerUuid
    session_id: SessionId
    timestamp: Timestamp
    version: VersionString
    platform: PlatformName
    tool_name: ToolName | None = None
    prompt_text: Prompt | None = None
    success: SuccessFlag = SuccessFlag(True)
    duration_ms: DurationMs | None = None
    error_message: ErrorMessage | None = None
    blender_version: BlenderVersion | None = None
    metadata: Details | None = None
