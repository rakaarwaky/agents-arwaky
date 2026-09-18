"""Tool-domain value objects for the AES tool features."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSpec:
    """Resolved, immutable view of a manifest tool used by tool capabilities."""

    id: str
    category: str
    binary: str
    is_mcp: bool
    description: str
    path: str
    alias: str | None
    mcp_binary: str | None
    runner: str


@dataclass(frozen=True)
class InstallResult:
    """Outcome of a tool installation."""

    success: bool
    tool_id: str
    message: str


@dataclass(frozen=True)
class UpdateResult:
    """Outcome of a tool update."""

    success: bool
    tool_id: str
    message: str


@dataclass(frozen=True)
class UninstallResult:
    """Outcome of a tool uninstallation."""

    success: bool
    tool_id: str
    message: str
